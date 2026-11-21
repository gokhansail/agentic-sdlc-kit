const SHARE_URL = "https://share.example.invalid/v1/presets";
// Placeholder: the reference carries no real key. The host never resolves, so every share ends in the error text.
const SHARE_KEY = "{FAKE_KEY}";

// Sends the settings to the preset service and returns the code it answers with.
export async function sharePreset(settings) {
  let response;
  try {
    response = await fetch(SHARE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${SHARE_KEY}` },
      body: JSON.stringify(settings),
    });
  } catch {
    throw new Error("the preset service could not be reached");
  }
  if (!response.ok) throw new Error(`the preset service answered ${response.status}`);
  let answer;
  try {
    answer = await response.json();
  } catch {
    answer = null;
  }
  if (!answer || typeof answer.code !== "string" || answer.code === "") throw new Error("the preset service sent no code");
  return answer.code;
}
