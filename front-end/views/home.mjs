import {renderEach, renderOne, destroy} from "../lib/render.mjs";
import {
  state,
  getLogoutContainer,
  getLoginContainer,
  getProfileContainer,
  getTimelineContainer,
  getBloomFormContainer,
} from "../index.mjs";
import {createLogin, handleLogin} from "../components/login.mjs";
import {createLogout, handleLogout} from "../components/logout.mjs";
import {createProfile} from "../components/profile.mjs";
import {
  createBloomForm,
  handleBloomSubmit,
  handleTyping,
} from "../components/bloom-form.mjs";
import {createBloom} from "../components/bloom.mjs";

// Home view - logged in or not
function homeView() {
  destroy();

  if (state.isLoggedIn) {
    renderOne(
      {
        profileData: state.profiles.find((p) => p.username === state.currentUser),
        whoToFollow: state.whoToFollow,
        isLoggedIn: state.isLoggedIn,
      },
      getProfileContainer(),
      "profile-template",
      createProfile
    );
    renderEach(
      state.timelineBlooms,
      getTimelineContainer(),
      "bloom-template",
      createBloom
    );
    renderOne(
      state.isLoggedIn,
      getBloomFormContainer(),
      "bloom-form-template",
      createBloomForm
    );
    renderOne(
      state.isLoggedIn,
      getLogoutContainer(),
      "logout-template",
      createLogout
    );
    document
      .querySelector("[data-action='logout']")
      ?.addEventListener("click", handleLogout);
    document
      .querySelector("[data-form='bloom']")
      ?.addEventListener("submit", handleBloomSubmit);
    document.querySelector("textarea")?.addEventListener("input", handleTyping);
  } else {
    renderOne(
      state.isLoggedIn,
      getLoginContainer(),
      "login-template",
      createLogin
    );
    document
      .querySelector("[data-form='login']")
      ?.addEventListener("submit", handleLogin);
  }
}
export {homeView};
