// The call below is never run at import time, so the engine still imports in Node.
export function save(value) {
  return localStorage.setItem("last", value);
}
