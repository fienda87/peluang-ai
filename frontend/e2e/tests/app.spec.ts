import { test, expect } from "@playwright/test";

test.describe("Home / Feed", () => {
  test("should display the homepage with title", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("Peluang.ai");
  });

  test("should show recommendation cards or empty state", async ({ page }) => {
    await page.goto("/");
    const cards = page.locator(".card");
    const emptyState = page.locator("text=Belum ada rekomendasi");
    const hasCards = (await cards.count()) > 0;
    const hasEmpty = (await emptyState.count()) > 0;
    expect(hasCards || hasEmpty).toBeTruthy();
  });
});

test.describe("Explore", () => {
  test("should display explore page with search input", async ({ page }) => {
    await page.goto("/explore");
    await expect(page.locator("h1")).toContainText("Jelajahi");
    await expect(page.locator('input[name="q"]')).toBeVisible();
  });

  test("should search and show results or empty state", async ({ page }) => {
    await page.goto("/explore?q=beasiswa");
    const cards = page.locator(".card");
    const empty = page.locator("text=Tidak ada hasil");
    const hasCards = (await cards.count()) > 0;
    const hasEmpty = (await empty.count()) > 0;
    expect(hasCards || hasEmpty).toBeTruthy();
  });
});

test.describe("Opportunity Detail", () => {
  test("should show not found for invalid slug", async ({ page }) => {
    await page.goto("/opportunity/nonexistent-slug-xyz");
    await expect(page.locator("h1")).toContainText("tidak ditemukan");
  });
});

test.describe("Saved & Applied", () => {
  test("should display saved page", async ({ page }) => {
    await page.goto("/saved");
    await expect(page.locator("h1")).toContainText("Tersimpan");
  });

  test("should display applied page", async ({ page }) => {
    await page.goto("/applied");
    await expect(page.locator("h1")).toContainText("Dilamar");
  });
});

test.describe("Profile", () => {
  test("should display profile page", async ({ page }) => {
    await page.goto("/profile");
    await expect(page.locator("h1")).toContainText("Profil");
  });
});

test.describe("Navigation", () => {
  test("should navigate from home to explore", async ({ page }) => {
    await page.goto("/");
    await page.goto("/explore");
    await expect(page.locator("h1")).toContainText("Jelajahi");
  });

  test("should navigate back from explore to home", async ({ page }) => {
    await page.goto("/explore");
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("Peluang.ai");
  });
});
