// R2 validation probe -- TEMPORARY.
// Reproduces the `toYearMonthKey` defect deterministically, independent of the
// machine timezone, by forcing TZ before the process starts (see run command).
const dates = ["2026-01-01", "2026-03-01", "2026-12-01", "2026-01-15"];

console.log("TZ:", Intl.DateTimeFormat().resolvedOptions().timeZone);
console.log("offset(min):", new Date().getTimezoneOffset());
console.log("");
console.log("input        parsed-as-local              key        expected   verdict");
console.log("-".repeat(80));

let wrong = 0;
for (const input of dates) {
  const d = new Date(input); // ISO date-only => parsed as UTC midnight
  const key = d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
  const expected = input.slice(0, 7);
  const ok = key === expected;
  if (!ok) wrong += 1;
  console.log(
    input.padEnd(13) +
      d.toString().slice(0, 28).padEnd(30) +
      key.padEnd(11) +
      expected.padEnd(11) +
      (ok ? "ok" : "WRONG"),
  );
}

console.log("");
console.log("wrong keys:", wrong, "of", dates.length);
