import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const python = fileURLToPath(new URL("../../../../python/.venv/bin/python", import.meta.url));
const source = () =>
  execFileSync(python, [
    "-c",
    [
      "import io, sys",
      "from PIL import Image",
      "output = io.BytesIO()",
      "Image.new('RGB', (40, 20), 'green').save(output, 'PNG')",
      "sys.stdout.buffer.write(output.getvalue())",
    ].join("\n"),
  ]);

const pageErrors = new WeakMap();

test.beforeEach(async ({ page }) => {
  const errors = [];
  pageErrors.set(page, errors);
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(process.env.PLAYGROUND_BROWSER_URL);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
});

test.afterEach(async ({ page }) => {
  expect(pageErrors.get(page)).toEqual([]);
});

test("upload, resize, poll and download a real WebP image", async ({ page }, testInfo) => {
  await page.getByLabel("Изображение", { exact: true }).setInputFiles({
    name: "landscape.png",
    mimeType: "image/png",
    buffer: source(),
  });
  await page.getByLabel("Макс. ширина").fill("20");
  await page.getByLabel("Макс. высота").fill("20");
  await page.getByRole("combobox").selectOption("webp");
  await page.getByRole("button", { name: "Обработать изображение" }).click();
  const result = page.getByRole("listitem").filter({ hasText: "20 × 20" });
  await expect(result).toContainText("Готово", { timeout: 20_000 });
  const downloadPromise = page.waitForEvent("download");
  await result.getByRole("link", { name: "Скачать" }).click();
  const download = await downloadPromise;
  expect(await download.failure()).toBeNull();
  const path = testInfo.outputPath("result.webp");
  await download.saveAs(path);
  const properties = JSON.parse(
    execFileSync(
      python,
      [
        "-c",
        [
          "import json, sys",
          "from PIL import Image",
          "image = Image.open(sys.argv[1])",
          "image.load()",
          "print(json.dumps({'format': image.format, 'size': list(image.size)}))",
        ].join("\n"),
        path,
      ],
      { encoding: "utf8" },
    ),
  );
  expect(properties).toEqual({ format: "WEBP", size: [20, 10] });
  await testInfo.attach("downloaded image", { path, contentType: "image/webp" });
});

test("reject an oversized file before creating a job", async ({ page }) => {
  const uploads = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === "/api/jobs")
      uploads.push(request.url());
  });
  await page.getByLabel("Изображение", { exact: true }).setInputFiles({
    name: "oversized.png",
    mimeType: "image/png",
    buffer: Buffer.alloc(10 * 1024 * 1024 + 1),
  });
  await page.getByRole("button", { name: "Обработать изображение" }).click();
  await expect(page.locator("form").getByRole("alert")).toHaveText(
    "Файл должен быть не больше 10 МиБ.",
  );
  expect(uploads).toEqual([]);
});

test("show processing failure for corrupt image content", async ({ page }) => {
  await page.getByLabel("Изображение", { exact: true }).setInputFiles({
    name: "corrupt.png",
    mimeType: "image/png",
    buffer: Buffer.from("this is not an image"),
  });
  await page.getByRole("button", { name: "Обработать изображение" }).click();
  const failure = page.getByRole("listitem").filter({ hasText: "Ошибка" });
  await expect(failure).toBeVisible({ timeout: 20_000 });
  await expect(failure.getByRole("link", { name: "Скачать" })).toHaveCount(0);
});
