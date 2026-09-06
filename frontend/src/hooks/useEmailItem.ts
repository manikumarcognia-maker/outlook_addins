import { useEffect, useState } from "react";
import type { EmailContext } from "../types";
import { extractDomain, sanitizeText, truncateText } from "../utils/sanitize";
import { waitForOfficeReady } from "../utils/officeReady";

function getBodyAsync(item: Office.MessageRead): Promise<string> {
  return new Promise((resolve, reject) => {
    item.body.getAsync(Office.CoercionType.Text, (result) => {
      if (result.status === Office.AsyncResultStatus.Succeeded) {
        resolve(result.value || "");
      } else {
        reject(new Error(result.error?.message || "Could not read email body."));
      }
    });
  });
}

async function readEmailContext(): Promise<EmailContext> {
  const item = Office.context.mailbox.item;

  if (!item || item.itemType !== Office.MailboxEnums.ItemType.Message) {
    throw new Error("Open an email message to use this add-in.");
  }

  const readItem = item as Office.MessageRead;
  const bodyRaw = await getBodyAsync(readItem);
  const senderEmail = readItem.from?.emailAddress || "";
  const senderName = sanitizeText(readItem.from?.displayName || "");
  const subject = sanitizeText(readItem.subject || "(no subject)");
  const body = truncateText(sanitizeText(bodyRaw));

  return {
    subject,
    body,
    senderEmail,
    senderName,
    senderDomain: extractDomain(senderEmail),
  };
}

export function useEmailItem() {
  const [email, setEmail] = useState<EmailContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        await waitForOfficeReady();
        const context = await readEmailContext();

        if (!cancelled) {
          setEmail(context);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setEmail(null);
          setError(err instanceof Error ? err.message : "Failed to read email.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    async function onItemChanged() {
      if (cancelled || !Office.context.mailbox.item) return;
      await load();
    }

    let handlerRegistered = false;

    async function setup() {
      await waitForOfficeReady();
      await load();

      Office.context.mailbox.addHandlerAsync(
        Office.EventType.ItemChanged,
        onItemChanged,
        () => {
          handlerRegistered = true;
        }
      );
    }

    setup();
    return () => {
      cancelled = true;
      if (
        handlerRegistered &&
        typeof Office !== "undefined" &&
        Office.context?.mailbox
      ) {
        Office.context.mailbox.removeHandlerAsync(
          Office.EventType.ItemChanged,
          onItemChanged
        );
      }
    };
  }, []);

  return { email, loading, error };
}

export function insertDraftIntoReply(draft: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const item = Office.context.mailbox.item as Office.MessageRead | undefined;
    if (!item || !item.displayReplyForm) {
      reject(new Error("Cannot open reply form for this item."));
      return;
    }

    const htmlBody = draft
      .split("\n")
      .map((line) => `<p>${line || "&nbsp;"}</p>`)
      .join("");

    item.displayReplyForm({
      htmlBody,
    });

    resolve();
  });
}
