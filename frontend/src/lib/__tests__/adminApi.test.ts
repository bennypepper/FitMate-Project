import { describe, it, expect } from "vitest";
import { isTokenExpired } from "@/lib/adminApi";

function toBase64Url(input: string): string {
  return Buffer.from(input, "utf8")
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function makeJwt(payload: Record<string, unknown>): string {
  const header = toBase64Url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = toBase64Url(JSON.stringify(payload));
  return `${header}.${body}.signature`;
}

describe("isTokenExpired", () => {
  it("returns false for a valid Base64URL JWT with '-', '_' and no '=' padding", () => {
    const futureExp = Math.floor(Date.now() / 1000) + 3600;
    // Choose a payload whose base64 encoding contains '+' and '/' and requires '=' padding
    const payload = {
      sub: "admin?>?>?>",
      note: "subjects?_d",
      exp: futureExp,
    };
    const token = makeJwt(payload);
    const bodySegment = token.split(".")[1];

    expect(bodySegment).toMatch(/[-_]/);
    expect(bodySegment.endsWith("=")).toBe(false);
    expect(isTokenExpired(token)).toBe(false);
  });

  it("returns true for an expired Base64URL JWT with '-' and '_'", () => {
    const pastExp = Math.floor(Date.now() / 1000) - 60;
    const payload = {
      sub: "admin?>?>?>",
      note: "subjects?_d",
      exp: pastExp,
    };
    const token = makeJwt(payload);
    expect(isTokenExpired(token)).toBe(true);
  });

  it("returns true for malformed or empty tokens", () => {
    expect(isTokenExpired("")).toBe(true);
    expect(isTokenExpired("not-a-jwt")).toBe(true);
    expect(isTokenExpired("header.!!!invalid!!!.sig")).toBe(true);
  });
});
