import {apiService} from "../lib/api.mjs";

/**
 * Create a bloom component
 * @param {string} template - The ID of the template to clone
 * @param {Object} bloom - The bloom data
 * @returns {DocumentFragment} - The bloom fragment of UI, for items in the Timeline
 * btw a bloom object is composed thus
 * {"id": Number,
 * "sender": username,
 * "content": "string from textarea",
 * "sent_timestamp": "datetime as ISO 8601 formatted string"}

 */
const createBloom = (template, bloom) => {
  if (!bloom) return;
  const bloomFrag = document.getElementById(template).content.cloneNode(true);
  const bloomParser = new DOMParser();

  const bloomArticle = bloomFrag.querySelector("[data-bloom]");
  // Attach the rebloom handler to this Bloom's own button.
  const rebloomButton = bloomFrag.querySelector("[data-action='rebloom']");
  rebloomButton?.addEventListener("click", handleRebloom);
  const bloomUsername = bloomFrag.querySelector("[data-username]");
  // Show who rebloomed the original Bloom when this timeline item is a rebloom.
  if (bloom.rebloomer) {
    const rebloomLabel = document.createElement("p");
    rebloomLabel.textContent = `${bloom.rebloomer} rebloomed`;
    rebloomLabel.classList.add("bloom__rebloom");
    bloomArticle.prepend(rebloomLabel);
  }
  // Shows the rebloom count only when the Bloom has been rebloomed.
  if (bloom.rebloom_count > 0) {
    const rebloomCount = document.createElement("p");
    rebloomCount.textContent = `${bloom.rebloom_count} rebloom${
      bloom.rebloom_count === 1 ? "" : "s"
    }`;
    rebloomCount.classList.add("bloom__rebloom-count");
    bloomArticle.append(rebloomCount);
  }
  const bloomTime = bloomFrag.querySelector("[data-time]");
  const bloomTimeLink = bloomFrag.querySelector("a:has(> [data-time])");
  const bloomContent = bloomFrag.querySelector("[data-content]");

  bloomArticle.setAttribute("data-bloom-id", bloom.id);
  bloomUsername.setAttribute("href", `/profile/${bloom.sender}`);
  bloomUsername.textContent = bloom.sender;
  bloomTime.textContent = _formatTimestamp(bloom.sent_timestamp);
  bloomTimeLink.setAttribute("href", `/bloom/${bloom.id}`);
  bloomContent.replaceChildren(
    ...bloomParser.parseFromString(_formatHashtags(bloom.content), "text/html")
      .body.childNodes
  );

  return bloomFrag;
};

// Sends the selected Bloom ID to the backend when the user clicks Rebloom.
async function handleRebloom(event) {
  const bloomArticle = event.currentTarget.closest("[data-bloom]");
  const bloomId = Number(bloomArticle?.dataset.bloomId);

  if (!bloomId) return;

  await apiService.postRebloom(bloomId);
}

function _formatHashtags(text) {
  if (!text) return text;
  return text.replace(
    /\B#[^#]+/g,
    (match) => `<a href="/hashtag/${match.slice(1)}">${match}</a>`
  );
}

function _formatTimestamp(timestamp) {
  if (!timestamp) return "";

  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffSeconds = Math.floor((now - date) / 1000);

    // Less than a minute
    if (diffSeconds < 60) {
      return `${diffSeconds}s`;
    }

    // Less than an hour
    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) {
      return `${diffMinutes}m`;
    }

    // Less than a day
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) {
      return `${diffHours}h`;
    }

    // Less than a week
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) {
      return `${diffDays}d`;
    }

    // Format as month and day for older dates
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
    }).format(date);
  } catch (error) {
    console.error("Failed to format timestamp:", error);
    return "";
  }
}

export {createBloom, handleRebloom};
