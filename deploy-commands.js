import "dotenv/config";
import { REST, Routes, SlashCommandBuilder, PermissionFlagsBits } from "discord.js";

function requireEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is missing in .env`);
  return value;
}

const BOT_TOKEN = requireEnv("BOT_TOKEN");
const CLIENT_ID = requireEnv("CLIENT_ID");
const GUILD_ID = requireEnv("GUILD_ID");
const ADMIN_ONLY = String(process.env.ADMIN_ONLY || "false").toLowerCase() === "true";

const submitPanel = new SlashCommandBuilder()
  .setName("writeup-submit-panel")
  .setDescription("Send the write-up upload panel.");

const writeupSite = new SlashCommandBuilder()
  .setName("writeup-site")
  .setDescription("Get the write-up website link.");

if (ADMIN_ONLY) {
  submitPanel.setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild);
}

const commands = [submitPanel, writeupSite].map((command) => command.toJSON());

const rest = new REST({ version: "10" }).setToken(BOT_TOKEN);

console.log("Registering slash commands...");
console.log(`Guild ID: ${GUILD_ID}`);
console.log(`Commands: ${commands.map((cmd) => "/" + cmd.name).join(", ")}`);

await rest.put(Routes.applicationGuildCommands(CLIENT_ID, GUILD_ID), { body: commands });

console.log("Slash commands registered successfully.");
