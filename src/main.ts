import { getWindow } from "@tauri-apps/api/window";

window.addEventListener("DOMContentLoaded", () => {
  const openSettingsBtn = document.querySelector("#open-settings");
  const openStatusBtn = document.querySelector("#open-status");
  
  openSettingsBtn?.addEventListener("click", async () => {
    const settingsWindow = getWindow("settings");
    if (settingsWindow) {
      await settingsWindow.show();
      await settingsWindow.setFocus();
    }
  });
  
  openStatusBtn?.addEventListener("click", async () => {
    const statusWindow = getWindow("status");
    if (statusWindow) {
      await statusWindow.show();
      await statusWindow.setFocus();
    }
  });
});
