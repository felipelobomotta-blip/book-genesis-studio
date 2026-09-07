"use strict";
// A post-action refresh must run after any request started before that action.
function createStudioRefresh(load) {
  let current = null;
  function refresh(force = false) {
    if (current) return force ? current.then(() => refresh()) : current;
    current = Promise.resolve().then(load).finally(() => { current = null; });
    return current;
  }
  return refresh;
}
if (typeof module !== "undefined") module.exports = {createStudioRefresh};
