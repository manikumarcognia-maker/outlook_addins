export function waitForOfficeReady(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof Office === "undefined") {
      reject(new Error("Office.js is not available. Open this add-in inside Outlook."));
      return;
    }
    Office.onReady((info) => {
      if (info.host === Office.HostType.Outlook) {
        resolve();
      } else {
        reject(new Error("This add-in only runs in Outlook."));
      }
    });
  });
}

export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
