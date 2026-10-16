import datetime

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from data.connection import db_cursor
from data.users import User

from psycopg2.errors import UniqueViolation


@dataclass
class Bloom:
    id: int
    sender: User
    content: str
    sent_timestamp: datetime.datetime


# Keeps rebloom information separate from the original Bloom data.
@dataclass
class Rebloom:
    bloom_id: int
    user: User
    rebloom_timestamp: datetime.datetime


# Extends Bloom data with rebloom information needed by the home timeline.
@dataclass
class TimelineBloom:
    id: int
    sender: User
    content: str
    sent_timestamp: datetime.datetime
    rebloomer: Optional[str] = None
    rebloom_timestamp: Optional[datetime.datetime] = None
    rebloom_count: int = 0


# Records a user's rebloom without creating another copy of the original Bloom.
def add_rebloom(*, bloom_id: int, user: User):
    rebloom_timestamp = datetime.datetime.now(datetime.UTC)

    with db_cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO reblooms (bloom_id, user_id, rebloom_timestamp) VALUES (%(bloom_id)s, %(user_id)s, %(rebloom_timestamp)s)",
                dict(
                    bloom_id=bloom_id,
                    user_id=user.id,
                    rebloom_timestamp=rebloom_timestamp,
                ),
            )
        except UniqueViolation:
            # Already rebloomed - treat as an idempotent request.
            pass


# Counts how many users have rebloomed the specified Bloom.
def get_rebloom_count(bloom_id: int) -> int:
    with db_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM reblooms WHERE bloom_id = %s",
            (bloom_id,),
        )
        row = cur.fetchone()
        return row[0]


# Gets the users who have rebloomed the specified Bloom.
def get_reblooms(bloom_id: int) -> List[Rebloom]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT reblooms.bloom_id, users.username, reblooms.rebloom_timestamp
            FROM reblooms
            INNER JOIN users ON users.id = reblooms.user_id
            WHERE reblooms.bloom_id = %s
            ORDER BY reblooms.rebloom_timestamp
            """,
            (bloom_id,),
        )
        rows = cur.fetchall()

        reblooms = []
        for row in rows:
            bloom_id, username, timestamp = row
            reblooms.append(
                Rebloom(
                    bloom_id=bloom_id,
                    user=username,
                    rebloom_timestamp=timestamp,
                )
            )

    return reblooms


# Gets the reblooms made by a specific user for their timeline.
def get_reblooms_for_user(username: str) -> List[Rebloom]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT reblooms.bloom_id, users.username, reblooms.rebloom_timestamp
            FROM reblooms
            INNER JOIN users ON users.id = reblooms.user_id
            WHERE users.username = %s
            ORDER BY reblooms.rebloom_timestamp DESC
            """,
            (username,),
        )
        rows = cur.fetchall()

        reblooms = []
        for row in rows:
            bloom_id, username, timestamp = row
            reblooms.append(
                Rebloom(
                    bloom_id=bloom_id,
                    user=username,
                    rebloom_timestamp=timestamp,
                )
            )

    return reblooms


def add_bloom(*, sender: User, content: str) -> Bloom:
    hashtags = [word[1:] for word in content.split(" ") if word.startswith("#")]

    now = datetime.datetime.now(tz=datetime.UTC)
    bloom_id = int(now.timestamp() * 1000000)
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO blooms (id, sender_id, content, send_timestamp) VALUES (%(bloom_id)s, %(sender_id)s, %(content)s, %(timestamp)s)",
            dict(
                bloom_id=bloom_id,
                sender_id=sender.id,
                content=content,
                timestamp=datetime.datetime.now(datetime.UTC),
            ),
        )
        for hashtag in hashtags:
            cur.execute(
                "INSERT INTO hashtags (hashtag, bloom_id) VALUES (%(hashtag)s, %(bloom_id)s)",
                dict(hashtag=hashtag, bloom_id=bloom_id),
            )


def get_blooms_for_user(
    username: str, *, before: Optional[int] = None, limit: Optional[int] = None
) -> List[Bloom]:
    with db_cursor() as cur:
        kwargs = {
            "sender_username": username,
        }
        if before is not None:
            before_clause = "AND send_timestamp < %(before_limit)s"
            kwargs["before_limit"] = before
        else:
            before_clause = ""

        limit_clause = make_limit_clause(limit, kwargs)

        cur.execute(
            f"""SELECT
              blooms.id, users.username, content, send_timestamp
            FROM
              blooms INNER JOIN users ON users.id = blooms.sender_id
            WHERE
              username = %(sender_username)s
              {before_clause}
            ORDER BY send_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        rows = cur.fetchall()
        blooms = []
        for row in rows:
            bloom_id, sender_username, content, timestamp = row
            blooms.append(
                Bloom(
                    id=bloom_id,
                    sender=sender_username,
                    content=content,
                    sent_timestamp=timestamp,
                )
            )
    return blooms


def get_bloom(bloom_id: int) -> Optional[Bloom]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT blooms.id, users.username, content, send_timestamp FROM blooms INNER JOIN users ON users.id = blooms.sender_id WHERE blooms.id = %s",
            (bloom_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        bloom_id, sender_username, content, timestamp = row
        return Bloom(
            id=bloom_id,
            sender=sender_username,
            content=content,
            sent_timestamp=timestamp,
        )


def get_blooms_with_hashtag(
    hashtag_without_leading_hash: str, *, limit: int = None
) -> List[Bloom]:
    kwargs = {
        "hashtag_without_leading_hash": hashtag_without_leading_hash,
    }
    limit_clause = make_limit_clause(limit, kwargs)
    with db_cursor() as cur:
        cur.execute(
            f"""SELECT
              blooms.id, users.username, content, send_timestamp
            FROM
              blooms INNER JOIN hashtags ON blooms.id = hashtags.bloom_id INNER JOIN users ON blooms.sender_id = users.id
            WHERE
              hashtag = %(hashtag_without_leading_hash)s
            ORDER BY send_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        rows = cur.fetchall()
        blooms = []
        for row in rows:
            bloom_id, sender_username, content, timestamp = row
            blooms.append(
                Bloom(
                    id=bloom_id,
                    sender=sender_username,
                    content=content,
                    sent_timestamp=timestamp,
                )
            )
    return blooms


def make_limit_clause(limit: Optional[int], kwargs: Dict[Any, Any]) -> str:
    if limit is not None:
        limit_clause = "LIMIT %(limit)s"
        kwargs["limit"] = limit
    else:
        limit_clause = ""
    return limit_clause
