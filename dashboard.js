/* jshint esversion: 8 */

document.getElementById("add_telegram_group").addEventListener(
  "click",
  async ev => {
    const response = await fetch("/api/v1/telegramdeeplink");
    if (!response.ok) {
      const errorP = document.createElement("p");
      const errorText = document.createTextNode("Error adding Telegram group");
      const okButton = document.createElement("button");
      const okText = document.createTextNode("OK");
      okButton.appendChild(okText);
      errorP.appendChild(errorText);
      errorP.appendChild(okButton);
      document.body.appendChild(errorP);
      okButton.addEventListener("click", (ev) => {
        document.body.removeChild(errorP);
      });
      return;
    }
    const responseJson = await response.json();
    const deeplinkA = document.createElement("a");
    deeplinkA.appendChild(document.createTextNode("Add Telegram group"));
    deeplinkA.setAttribute("href", responseJson.deeplinkUrl);
    document.body.appendChild(deeplinkA);
  }
);
