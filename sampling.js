// sampling.js — force fixed sampling params on every provider request.
//
// Pi has no CLI flag for temperature/top_p/etc; the `before_provider_request`
// hook (see docs/extensions.md) is the supported way to set them per-request.
// Values come from env so the benchmark can record/sweep them without editing
// this file. Anything unset is left to the provider/LM Studio default.
//
// Env (all optional):
//   PI_SAMPLING_TEMPERATURE, PI_SAMPLING_TOP_P, PI_SAMPLING_TOP_K,
//   PI_SAMPLING_MIN_P, PI_SAMPLING_PRESENCE_PENALTY, PI_SAMPLING_REPEAT_PENALTY
//
// Loaded with:  pi -e sampling.js ...

function num(name) {
  const v = process.env[name];
  if (v === undefined || v === "") return undefined;
  const n = Number(v);
  return Number.isNaN(n) ? undefined : n;
}

// Map our env names -> the payload keys the provider expects. LM Studio / OpenAI
// style uses snake_case; llama.cpp accepts top_k/min_p/repeat_penalty too.
function params() {
  return {
    temperature: num("PI_SAMPLING_TEMPERATURE"),
    top_p: num("PI_SAMPLING_TOP_P"),
    top_k: num("PI_SAMPLING_TOP_K"),
    min_p: num("PI_SAMPLING_MIN_P"),
    presence_penalty: num("PI_SAMPLING_PRESENCE_PENALTY"),
    repeat_penalty: num("PI_SAMPLING_REPEAT_PENALTY"),
  };
}

export default function (pi) {
  pi.on("before_provider_request", (event) => {
    const patch = {};
    for (const [k, v] of Object.entries(params())) {
      if (v !== undefined) patch[k] = v;
    }
    if (Object.keys(patch).length === 0) return; // nothing to override
    return { ...event.payload, ...patch };
  });
}
