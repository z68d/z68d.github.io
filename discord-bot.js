import "dotenv/config";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  Client,
  Events,
  GatewayIntentBits,
  Partials,
} from "discord.js";

const ROOT = process.cwd();
const BOT_TOKEN = requireEnv("BOT_TOKEN");
const SITE_URL = stripTrailingSlash(process.env.SITE_URL || "https://z68d.github.io");
const COMPETITION_NAME = process.env.COMPETITION_NAME || "Midnight Sun CTF 2026 Quals";
const COMPETITION_SLUG = process.env.COMPETITION_SLUG || "midnight-sun-ctf-2026-quals";
const WRITEUPS_DIR = process.env.WRITEUPS_DIR || "Midnight Sun CTF 2026 Quals";
const ADMIN_ONLY = String(process.env.ADMIN_ONLY || "false").toLowerCase() === "true";
const MAX_MD_BYTES = 1024 * 1024;

const pendingUploads = new Map();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.DirectMessages,
    GatewayIntentBits.MessageContent,
  ],
  partials: [Partials.Channel],
});

client.once(Events.ClientReady, (readyClient) => {
  console.log(`Discord bot logged in as ${readyClient.user.tag}`);
  console.log(`Upload target: ${WRITEUPS_DIR}/ -> ${SITE_URL}/${COMPETITION_SLUG}/`);
});

client.on(Events.InteractionCreate, async (interaction) => {
  try {
    if (interaction.isChatInputCommand()) {
      if (interaction.commandName === "writeup-submit-panel") {
        if (ADMIN_ONLY && !interaction.memberPermissions?.has("ManageGuild")) {
          await interaction.reply({ content: "You do not have permission to use this command.", flags: 64 });
          return;
        }

        const uploadButton = new ButtonBuilder()
          .setCustomId("writeup_upload_start")
          .setLabel("Upload writeup.md")
          .setStyle(ButtonStyle.Primary)
          .setEmoji("📄");

        const siteButton = new ButtonBuilder()
          .setLabel("Open site")
          .setStyle(ButtonStyle.Link)
          .setURL(`${SITE_URL}/${COMPETITION_SLUG}/`)
          .setEmoji("🌐");

        const row = new ActionRowBuilder().addComponents(uploadButton, siteButton);

        await interaction.reply({
          content: [
            "**SAAD CTF Write-ups**",
            "",
            `Competition: **${COMPETITION_NAME}**`,
            "Click the button below, then send your `writeup.md` file in DM.",
          ].join("\n"),
          components: [row],
        });
        return;
      }

      if (interaction.commandName === "writeup-site") {
        await interaction.reply({ content: `${SITE_URL}/${COMPETITION_SLUG}/`, flags: 64 });
        return;
      }
    }

    if (interaction.isButton() && interaction.customId === "writeup_upload_start") {
      const dm = await interaction.user.createDM().catch(() => null);
      if (!dm) {
        await interaction.reply({
          content: "I could not DM you. Enable DMs from server members and try again.",
          flags: 64,
        });
        return;
      }

      pendingUploads.set(interaction.user.id, {
        expiresAt: Date.now() + 10 * 60 * 1000,
      });

      await dm.send([
        "**Upload writeup.md**",
        "",
        `Competition: **${COMPETITION_NAME}**`,
        "Send the markdown file as an attachment named `writeup.md` or `*_writeup.md`.",
        "The bot will add it to the website, rebuild the static pages, commit, and push to GitHub.",
        "You have 10 minutes.",
      ].join("\n"));

      await interaction.reply({ content: "I sent you a DM. Send the write-up file there.", flags: 64 });
      return;
    }
  } catch (error) {
    console.error(error);
    const payload = { content: "Unexpected error while handling the interaction.", flags: 64 };
    if (interaction.replied || interaction.deferred) {
      await interaction.followUp(payload).catch(() => {});
    } else {
      await interaction.reply(payload).catch(() => {});
    }
  }
});

client.on(Events.MessageCreate, async (message) => {
  try {
    if (message.author.bot) return;
    if (message.guildId) return;

    const pending = pendingUploads.get(message.author.id);
    if (!pending) {
      if (["help", "upload"].includes(message.content.trim().toLowerCase())) {
        await message.reply("Use the server upload panel, then send me your `writeup.md` file here.");
      }
      return;
    }

    if (Date.now() > pending.expiresAt) {
      pendingUploads.delete(message.author.id);
      await message.reply("Upload session expired. Click the upload button again.");
      return;
    }

    const attachment = [...message.attachments.values()].find((item) =>
      item.name?.toLowerCase().endsWith(".md")
    );

    if (!attachment) {
      await message.reply("Please attach a markdown file ending with `.md`.");
      return;
    }

    if (attachment.size > MAX_MD_BYTES) {
      await message.reply("That markdown file is too large. Max size is 1 MB.");
      return;
    }

    await message.reply("Received. Building and pushing the site now...");

    const markdown = await downloadText(attachment.url);
    const challengeName = extractChallengeName(markdown) || path.basename(attachment.name, ".md");
    const challengeSlug = slugify(challengeName);
    const fileName = `${challengeSlug}_writeup.md`;
    const writeupsPath = path.join(ROOT, WRITEUPS_DIR);
    const targetPath = path.join(writeupsPath, fileName);

    fs.mkdirSync(writeupsPath, { recursive: true });
    fs.writeFileSync(targetPath, normalizeMarkdown(markdown), "utf8");

    const output = rebuildCommitPush(challengeName);
    pendingUploads.delete(message.author.id);

    await message.reply([
      "Done. The write-up was uploaded and pushed.",
      "",
      `Challenge: **${challengeName}**`,
      `File: \`${WRITEUPS_DIR}/${fileName}\``,
      `Link: ${SITE_URL}/${COMPETITION_SLUG}/ch/${challengeSlug}/index.html`,
      "",
      "```txt",
      output.slice(-1500),
      "```",
    ].join("\n"));
  } catch (error) {
    console.error(error);
    await message.reply([
      "Upload failed.",
      "",
      "```txt",
      String(error?.message || error).slice(0, 1500),
      "```",
    ].join("\n")).catch(() => {});
  }
});

function rebuildCommitPush(challengeName) {
  const logs = [];

  run("python3", ["build_site.py"], logs);
  run("git", ["add", "."], logs);

  const status = execFileSync("git", ["status", "--porcelain"], {
    cwd: ROOT,
    encoding: "utf8",
  }).trim();

  if (!status) {
    logs.push("No git changes to commit.");
    return logs.join("\n");
  }

  const safeName = challengeName.replace(/[\r\n]+/g, " ").slice(0, 80);
  run("git", ["commit", "-m", `Add writeup: ${safeName}`], logs);
  run("git", ["push"], logs);

  return logs.join("\n");
}

function run(command, args, logs) {
  logs.push(`$ ${command} ${args.join(" ")}`);
  const output = execFileSync(command, args, {
    cwd: ROOT,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  if (output.trim()) logs.push(output.trim());
}

async function downloadText(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to download attachment: HTTP ${response.status}`);
  const text = await response.text();
  return text.replace(/^\uFEFF/, "");
}

function normalizeMarkdown(text) {
  return text.replace(/\r\n/g, "\n").trimEnd() + "\n";
}

function extractChallengeName(markdown) {
  const nameMatch = markdown.match(/^Name:\s*(.+)$/im);
  if (nameMatch) return nameMatch[1].trim();

  const titleMatch = markdown.match(/^#\s+(.+)$/m);
  if (titleMatch) return titleMatch[1].trim();

  return "";
}

function slugify(value) {
  return String(value)
    .toLowerCase()
    .trim()
    .replace(/['"]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "writeup";
}

function requireEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is missing in .env`);
  return value;
}

function stripTrailingSlash(value) {
  return String(value).replace(/\/+$/, "");
}

await client.login(BOT_TOKEN);
