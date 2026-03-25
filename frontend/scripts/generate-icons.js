const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const publicDir = path.join(__dirname, "..", "public");
const iconPath = path.join(publicDir, "icon.png");
const iconsDir = path.join(publicDir, "icons");

if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

async function generateIcons() {
  try {
    await sharp(iconPath)
      .resize(192, 192)
      .toFile(path.join(iconsDir, "icon-192.png"));
    console.log("Generated icon-192.png");

    await sharp(iconPath)
      .resize(512, 512)
      .toFile(path.join(iconsDir, "icon-512.png"));
    console.log("Generated icon-512.png");
  } catch (error) {
    console.error("Error generating icons:", error);
  }
}

generateIcons();
