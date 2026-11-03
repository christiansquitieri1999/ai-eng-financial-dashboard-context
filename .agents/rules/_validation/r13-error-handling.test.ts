// R13 probe. The catch handler lives inside a React effect, so it cannot be
// reached by rendering (effects never run during static/server rendering).
// Instead this asserts on the source contract: the status IS built, then IS
// discarded. Both facts must hold for the rule to be accurate.
//
// NOTE: the source is imported with Vite's `?raw` suffix rather than read via
// node:fs. `tsconfig.app.json` sets "types": ["vite/client"], so Node builtins
// are not typed inside src/ — importing node:fs here fails the type check with
// TS2591. `?raw` is typed by vite/client and keeps `npm run build` green.
//
// This file lives outside `frontend/` (in `.agents/rules/_validation/`), so the
// import climbs three levels back to the app source. It is discovered by
// passing `--dir` to Vitest; see `README.md` for the exact command. Running a
// bare `npx vitest run` in `frontend/` will NOT find this file.

import { describe, expect, it } from "vitest";
import appSource from "../../../frontend/src/App.tsx?raw";

describe("R13 - error preservation and UI language", () => {
  it("builds an error that carries the HTTP status", () => {
    // fetchFinancialData constructs a useful error...
    expect(appSource).toContain("Failed to fetch financial data: ${response.status}");
  });

  it("discards that error with a zero-argument catch handler", () => {
    // ...and the handler takes no parameter, so the error is unreachable.
    expect(appSource).toContain(".catch(() => {");

    // The discarded error is never bound anywhere.
    expect(appSource).not.toMatch(/\.catch\(\s*\(\s*\w+\s*\)/);
    expect(appSource).not.toMatch(/\.catch\(\s*\w+\s*=>/);
  });

  it("replaces it with a fixed string containing no status information", () => {
    const match = appSource.match(/setError\(\s*\n?\s*"([^"]+)"/);
    expect(match).not.toBeNull();
    const message = match![1];

    // No interpolation: the status cannot survive into the message.
    expect(message).not.toContain("${");
    expect(message).not.toMatch(/\d{3}/); // no status code
    expect(message).not.toContain("response");
  });

  it("uses a language unlike the rest of the UI", () => {
    const match = appSource.match(/setError\(\s*\n?\s*"([^"]+)"/);
    const message = match![1];

    expect(message).toContain("No se pudo cargar");
    expect(message).toContain("Revisa la API de backend");

    // Every other user-facing string in this file is English.
    expect(appSource).toContain('period="2024 - Full Year"');

    // The text is unaccented Spanish. Correct Spanish is "información";
    // the shipped text is "informacion", so even a Spanish-speaking user
    // reads it as machine-generated.
    expect(message).toContain("informacion");
    expect(message).not.toContain("información");
  });
});
