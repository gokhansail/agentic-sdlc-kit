import { save as store } from "./deep.js";

export function save(value) {
  return store(value);
}
