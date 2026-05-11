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
  ModalBuilder,
  Partials,
  StringSelectMenuBuilder,
  TextInputBuilder,
  TextInputStyle,
} from "discord.js";

const ROOT = process.cwd();
const BOT_TOKEN = requireEnv("BOT_TOKEN");
const SITE_URL = stripTrailingSlash(process.env.SITE_URL || "https://z68d.github.io");
const ADMIN_ONLY = String(process.env.ADMIN_ONLY || "false").toLowerCase() === "true";
const MAX_MD_BYTES = 1024 * 1024;
const COMPETITIONS_FILE = path.join(ROOT, "competitions.json");
const DEFAULT_COMPETITION = {
  name: "Midnight Sun CTF 2026 Quals",
  slug: "midnight-sun-ctf-2026-quals",
  dir: "Midnight Sun CTF 2026 Quals",
};

const pendingUploads = new Map();
const pendingDeletes = new Map();

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
  console.log(`Site URL: ${SITE_URL}`);
  console.log(`Competitions: ${loadCompetitions().map((c) => c.name).join(", ")}`);
});

client.on(Events.InteractionCreate, async (interaction) => {
  try {
    if (interaction.isChatInputCommand()) {
      if (ADMIN_ONLY && !hasManageGuild(interaction)) {
        await interaction.reply({ content: "You do not have permission to use this command.", flags: 64 });
        return;
      }

      if (interaction.commandName === "writeup-submit-panel") {
        await sendWriteupPanel(interaction);
        return;
      }

      if (interaction.commandName === "writeup-site") {
        const comps = loadCompetitions();
        const lines = comps.map((comp) => `- **${comp.name}**: ${SITE_URL}/${comp.slug}/`);
        await interaction.reply({ content: lines.join("\n") || SITE_URL, flags: 64 });
        return;
      }

      if (interaction.commandName === "competition-add") {
        const name = interaction.options.getString("name", true).trim();
        const rawSlug = interaction.options.getString("slug")?.trim();
        await addCompetitionAndReply(interaction, name, rawSlug);
        return;
      }
    }

    if (interaction.isButton()) {
      if (ADMIN_ONLY && !hasManageGuild(interaction)) {
        await interaction.reply({ content: "You do not have permission to use this button.", flags: 64 });
        return;
      }

      if (interaction.customId === "writeup_upload_start") {
        await replyWithCompetitionSelect(interaction, "upload");
        return;
      }

      if (interaction.customId === "writeup_edit_start") {
        await replyWithCompetitionSelect(interaction, "edit");
        return;
      }

      if (interaction.customId === "writeup_delete_start") {
        await replyWithCompetitionSelect(interaction, "delete");
        return;
      }

      if (interaction.customId === "competition_add_start") {
        await showCompetitionModal(interaction);
        return;
      }

      if (interaction.customId === "delete_confirm") {
        await confirmDelete(interaction);
        return;
      }

      if (interaction.customId === "delete_cancel") {
        pendingDeletes.delete(interaction.user.id);
        await interaction.reply({ content: "Delete cancelled.", flags: 64 });
        return;
      }
    }

    if (interaction.isStringSelectMenu()) {
      if (ADMIN_ONLY && !hasManageGuild(interaction)) {
        await interaction.reply({ content: "You do not have permission to use this menu.", flags: 64 });
        return;
      }

      if (interaction.customId === "select_comp_upload") {
        await startUploadDm(interaction, interaction.values[0], "add");
        return;
      }

      if (interaction.customId === "select_comp_edit") {
        await replyWithChallengeSelect(interaction, interaction.values[0], "edit");
        return;
      }

      if (interaction.customId === "select_comp_delete") {
        await replyWithChallengeSelect(interaction, interaction.values[0], "delete");
        return;
      }

      if (interaction.customId.startsWith("select_challenge_edit:")) {
        const compSlug = interaction.customId.split(":", 2)[1];
        const challengeSlug = interaction.values[0];
        await startUploadDm(interaction, compSlug, "edit", challengeSlug);
        return;
      }

      if (interaction.customId.startsWith("select_challenge_delete:")) {
        const compSlug = interaction.customId.split(":", 2)[1];
        const challengeSlug = interaction.values[0];
        await askDeleteConfirm(interaction, compSlug, challengeSlug);
        return;
      }
    }

    if (interaction.isModalSubmit() && interaction.customId === "competition_add_modal") {
      if (ADMIN_ONLY && !hasManageGuild(interaction)) {
        await interaction.reply({ content: "You do not have permission to use this modal.", flags: 64 });
        return;
      }

      const name = interaction.fields.getTextInputValue("competition_name").trim();
      const rawSlug = interaction.fields.getTextInputValue("competition_slug")?.trim();
      await addCompetitionAndReply(interaction, name, rawSlug);
      return;
    }
  } catch (error) {
    console.error(error);
    const payload = { content: `Unexpected error: ${String(error?.message || error).slice(0, 1500)}`, flags: 64 };
    if (interaction.replied || interaction.deferred) await interaction.followUp(payload).catch(() => {});
    else await interaction.reply(payload).catch(() => {});
  }
});

client.on(Events.MessageCreate, async (message) => {
  try {
    if (message.author.bot) return;
    if (message.guildId) return;

    const pending = pendingUploads.get(message.author.id);
    if (!pending) {
      if (["help", "upload"].includes(message.content.trim().toLowerCase())) {
        await message.reply("Use the server write-up panel, choose a competition/action, then send me your markdown file here.");
      }
      return;
    }

    if (Date.now() > pending.expiresAt) {
      pendingUploads.delete(message.author.id);
      await message.reply("Upload session expired. Start again from the panel.");
      return;
    }

    const attachment = [...message.attachments.values()].find((item) => item.name?.toLowerCase().endsWith(".md"));
    if (!attachment) {
      await message.reply("Please attach a markdown file ending with `.md`.");
      return;
    }

    if (attachment.size > MAX_MD_BYTES) {
      await message.reply("That markdown file is too large. Max size is 1 MB.");
      return;
    }

    const comp = getCompetition(pending.compSlug);
    if (!comp) {
      pendingUploads.delete(message.author.id);
      await message.reply("Competition no longer exists. Start again from the panel.");
      return;
    }

    await message.reply(pending.mode === "edit" ? "Received. Updating the write-up now..." : "Received. Uploading the write-up now...");

    const markdown = await downloadText(attachment.url);
    const challengeName = extractChallengeName(markdown) || path.basename(attachment.name, ".md").replace(/_writeup$/i, "");
    const challengeSlug = pending.mode === "edit" && pending.challengeSlug ? pending.challengeSlug : slugify(challengeName);
    const fileName = pending.mode === "edit" && pending.fileName ? pending.fileName : `${challengeSlug}_writeup.md`;
    const writeupsPath = path.join(ROOT, comp.dir);
    const targetPath = path.join(writeupsPath, fileName);

    fs.mkdirSync(writeupsPath, { recursive: true });
    fs.writeFileSync(targetPath, normalizeMarkdown(markdown), "utf8");

    const actionText = pending.mode === "edit" ? "Update" : "Add";
    const output = rebuildCommitPush(`${actionText} writeup: ${challengeName}`);
    pendingUploads.delete(message.author.id);

    await message.reply([
      pending.mode === "edit" ? "Done. The write-up was updated and pushed." : "Done. The write-up was uploaded and pushed.",
      "",
      `Competition: **${comp.name}**`,
      `Challenge: **${challengeName}**`,
      `File: \`${comp.dir}/${fileName}\``,
      `Link: ${SITE_URL}/${comp.slug}/ch/${challengeSlug}/index.html`,
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

async function sendWriteupPanel(interaction) {
  const uploadButton = new ButtonBuilder()
    .setCustomId("writeup_upload_start")
    .setLabel("Upload writeup")
    .setStyle(ButtonStyle.Primary)
    .setEmoji("📄");

  const editButton = new ButtonBuilder()
    .setCustomId("writeup_edit_start")
    .setLabel("Edit writeup")
    .setStyle(ButtonStyle.Secondary)
    .setEmoji("✏️");

  const deleteButton = new ButtonBuilder()
    .setCustomId("writeup_delete_start")
    .setLabel("Delete writeup")
    .setStyle(ButtonStyle.Danger)
    .setEmoji("🗑️");

  const addCompetitionButton = new ButtonBuilder()
    .setCustomId("competition_add_start")
    .setLabel("Add competition")
    .setStyle(ButtonStyle.Success)
    .setEmoji("➕");

  const siteButton = new ButtonBuilder()
    .setLabel("Open site")
    .setStyle(ButtonStyle.Link)
    .setURL(SITE_URL)
    .setEmoji("🌐");

  const row1 = new ActionRowBuilder().addComponents(uploadButton, editButton, deleteButton, addCompetitionButton);
  const row2 = new ActionRowBuilder().addComponents(siteButton);

  const comps = loadCompetitions();
  await interaction.reply({
    content: [
      "**SAAD CTF Write-ups**",
      "",
      `Competitions: **${comps.length}**`,
      "Choose an action below.",
    ].join("\n"),
    components: [row1, row2],
  });
}

async function replyWithCompetitionSelect(interaction, mode) {
  const comps = loadCompetitions();
  if (!comps.length) {
    await interaction.reply({ content: "No competitions found. Add one first.", flags: 64 });
    return;
  }

  const select = new StringSelectMenuBuilder()
    .setCustomId(`select_comp_${mode}`)
    .setPlaceholder("Choose a competition")
    .addOptions(comps.slice(0, 25).map((comp) => ({
      label: comp.name.slice(0, 100),
      description: comp.slug.slice(0, 100),
      value: comp.slug,
    })));

  const row = new ActionRowBuilder().addComponents(select);
  await interaction.reply({ content: `Choose the competition for **${mode}**.`, components: [row], flags: 64 });
}

async function replyWithChallengeSelect(interaction, compSlug, mode) {
  const comp = getCompetition(compSlug);
  if (!comp) {
    await interaction.reply({ content: "Competition not found.", flags: 64 });
    return;
  }

  const writeups = listWriteups(comp);
  if (!writeups.length) {
    await interaction.reply({ content: `No write-ups found in **${comp.name}**.`, flags: 64 });
    return;
  }

  const select = new StringSelectMenuBuilder()
    .setCustomId(`select_challenge_${mode}:${comp.slug}`)
    .setPlaceholder("Choose a write-up")
    .addOptions(writeups.slice(0, 25).map((item) => ({
      label: item.name.slice(0, 100),
      description: item.fileName.slice(0, 100),
      value: item.slug,
    })));

  const row = new ActionRowBuilder().addComponents(select);
  await interaction.reply({ content: `Choose the write-up to **${mode}** from **${comp.name}**.`, components: [row], flags: 64 });
}

async function startUploadDm(interaction, compSlug, mode, challengeSlug = null) {
  const comp = getCompetition(compSlug);
  if (!comp) {
    await interaction.reply({ content: "Competition not found.", flags: 64 });
    return;
  }

  let selected = null;
  if (mode === "edit") {
    selected = listWriteups(comp).find((item) => item.slug === challengeSlug);
    if (!selected) {
      await interaction.reply({ content: "Write-up not found.", flags: 64 });
      return;
    }
  }

  const dm = await interaction.user.createDM().catch(() => null);
  if (!dm) {
    await interaction.reply({ content: "I could not DM you. Enable DMs from server members and try again.", flags: 64 });
    return;
  }

  pendingUploads.set(interaction.user.id, {
    mode,
    compSlug: comp.slug,
    challengeSlug: selected?.slug || null,
    fileName: selected?.fileName || null,
    expiresAt: Date.now() + 10 * 60 * 1000,
  });

  if (mode === "edit") {
    await dm.send([
      "**Edit write-up**",
      "",
      `Competition: **${comp.name}**`,
      `Selected: **${selected.name}**`,
      `Current file: \`${comp.dir}/${selected.fileName}\``,
      "Send the replacement markdown file as an attachment ending with `.md`.",
      "The bot will overwrite the selected write-up, rebuild the site, commit, and push.",
      "You have 10 minutes.",
    ].join("\n"));
  } else {
    await dm.send([
      "**Upload write-up**",
      "",
      `Competition: **${comp.name}**`,
      "Send the markdown file as an attachment named `writeup.md` or `*_writeup.md`.",
      "The bot will add it to this competition, rebuild the site, commit, and push.",
      "You have 10 minutes.",
    ].join("\n"));
  }

  await interaction.reply({ content: "I sent you a DM. Send the markdown file there.", flags: 64 });
}

async function showCompetitionModal(interaction) {
  const modal = new ModalBuilder()
    .setCustomId("competition_add_modal")
    .setTitle("Add competition");

  const nameInput = new TextInputBuilder()
    .setCustomId("competition_name")
    .setLabel("Competition name")
    .setPlaceholder("Midnight Sun CTF 2026 Quals")
    .setStyle(TextInputStyle.Short)
    .setRequired(true)
    .setMaxLength(100);

  const slugInput = new TextInputBuilder()
    .setCustomId("competition_slug")
    .setLabel("Slug / URL path (optional)")
    .setPlaceholder("midnight-sun-ctf-2026-quals")
    .setStyle(TextInputStyle.Short)
    .setRequired(false)
    .setMaxLength(100);

  modal.addComponents(
    new ActionRowBuilder().addComponents(nameInput),
    new ActionRowBuilder().addComponents(slugInput),
  );

  await interaction.showModal(modal);
}

async function addCompetitionAndReply(interaction, name, rawSlug) {
  if (!name) {
    await interaction.reply({ content: "Competition name is required.", flags: 64 });
    return;
  }

  const comps = loadCompetitions();
  const slug = slugify(rawSlug || name);
  if (comps.some((comp) => comp.slug === slug)) {
    await interaction.reply({ content: `Competition already exists: ${SITE_URL}/${slug}/`, flags: 64 });
    return;
  }

  const comp = { name, slug, dir: name };
  comps.push(comp);
  saveCompetitions(comps);
  fs.mkdirSync(path.join(ROOT, comp.dir), { recursive: true });

  const output = rebuildCommitPush(`Add competition: ${name}`);
  await interaction.reply({
    content: [
      "Competition added.",
      "",
      `Name: **${name}**`,
      `Directory: \`${comp.dir}\``,
      `Link: ${SITE_URL}/${slug}/`,
      "",
      "```txt",
      output.slice(-1200),
      "```",
    ].join("\n"),
    flags: 64,
  });
}

async function askDeleteConfirm(interaction, compSlug, challengeSlug) {
  const comp = getCompetition(compSlug);
  const selected = comp ? listWriteups(comp).find((item) => item.slug === challengeSlug) : null;
  if (!comp || !selected) {
    await interaction.reply({ content: "Write-up not found.", flags: 64 });
    return;
  }

  pendingDeletes.set(interaction.user.id, { compSlug, challengeSlug, fileName: selected.fileName, name: selected.name, expiresAt: Date.now() + 5 * 60 * 1000 });

  const confirm = new ButtonBuilder().setCustomId("delete_confirm").setLabel("Yes, delete").setStyle(ButtonStyle.Danger);
  const cancel = new ButtonBuilder().setCustomId("delete_cancel").setLabel("Cancel").setStyle(ButtonStyle.Secondary);
  const row = new ActionRowBuilder().addComponents(confirm, cancel);

  await interaction.reply({
    content: `Delete **${selected.name}** from **${comp.name}**?\nFile: \`${comp.dir}/${selected.fileName}\``,
    components: [row],
    flags: 64,
  });
}

async function confirmDelete(interaction) {
  const pending = pendingDeletes.get(interaction.user.id);
  if (!pending) {
    await interaction.reply({ content: "No pending delete request.", flags: 64 });
    return;
  }

  if (Date.now() > pending.expiresAt) {
    pendingDeletes.delete(interaction.user.id);
    await interaction.reply({ content: "Delete confirmation expired.", flags: 64 });
    return;
  }

  const comp = getCompetition(pending.compSlug);
  if (!comp) {
    pendingDeletes.delete(interaction.user.id);
    await interaction.reply({ content: "Competition not found.", flags: 64 });
    return;
  }

  const filePath = path.join(ROOT, comp.dir, pending.fileName);
  if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
  const output = rebuildCommitPush(`Delete writeup: ${pending.name}`);
  pendingDeletes.delete(interaction.user.id);

  await interaction.reply({
    content: [
      "Deleted and pushed.",
      "",
      `Competition: **${comp.name}**`,
      `Write-up: **${pending.name}**`,
      "",
      "```txt",
      output.slice(-1200),
      "```",
    ].join("\n"),
    flags: 64,
  });
}

function rebuildCommitPush(message) {
  const logs = [];
  run("python3", ["build_site.py"], logs);
  run("git", ["add", "."], logs);

  const status = execFileSync("git", ["status", "--porcelain"], { cwd: ROOT, encoding: "utf8" }).trim();
  if (!status) {
    logs.push("No git changes to commit.");
    return logs.join("\n");
  }

  const safeMessage = message.replace(/[\r\n]+/g, " ").slice(0, 100);
  run("git", ["commit", "-m", safeMessage], logs);
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
  return (await response.text()).replace(/^\uFEFF/, "");
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

function listWriteups(comp) {
  const writeupsPath = path.join(ROOT, comp.dir);
  if (!fs.existsSync(writeupsPath)) return [];

  return fs.readdirSync(writeupsPath)
    .filter((fileName) => fileName.toLowerCase().endsWith(".md"))
    .map((fileName) => {
      const fullPath = path.join(writeupsPath, fileName);
      const markdown = fs.readFileSync(fullPath, "utf8");
      const name = extractChallengeName(markdown) || fileName.replace(/_writeup\.md$/i, "").replace(/\.md$/i, "");
      return { name, slug: slugify(name), fileName };
    })
    .sort((a, b) => a.name.localeCompare(b.name));
}

function loadCompetitions() {
  if (!fs.existsSync(COMPETITIONS_FILE)) {
    saveCompetitions([DEFAULT_COMPETITION]);
  }

  const parsed = JSON.parse(fs.readFileSync(COMPETITIONS_FILE, "utf8"));
  return parsed.map((item) => ({
    name: String(item.name || "").trim(),
    slug: slugify(item.slug || item.name),
    dir: String(item.dir || item.name || "").trim(),
  })).filter((item) => item.name && item.slug && item.dir);
}

function saveCompetitions(comps) {
  fs.writeFileSync(COMPETITIONS_FILE, JSON.stringify(comps, null, 2) + "\n", "utf8");
}

function getCompetition(slug) {
  return loadCompetitions().find((comp) => comp.slug === slug);
}

function slugify(value) {
  return String(value)
    .toLowerCase()
    .trim()
    .replace(/[\'"]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "writeup";
}

function hasManageGuild(interaction) {
  return !ADMIN_ONLY || Boolean(interaction.memberPermissions?.has("ManageGuild"));
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
