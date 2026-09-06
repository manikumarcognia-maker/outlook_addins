import { getAccessToken } from "../auth";
import type {
  CustomerCreateInput,
  CustomerCreateResult,
  CustomerLookupInput,
  CustomerLookupResult,
} from "../types";
import { delay } from "../utils/officeReady";

/**
 * MOCK — swap for fetch('https://your-backend/verify-customer', ...) later.
 */
export async function lookupCustomer(input: CustomerLookupInput): Promise<CustomerLookupResult> {
  await getAccessToken();
  await delay(900);

  const mockFoundDomains = ["nexusfreight.com", "cogniaworks.onmicrosoft.com"];

  if (mockFoundDomains.includes(input.domain.toLowerCase())) {
    return {
      status: "found",
      profile: {
        name: input.displayName || "Nexus Freight Pte Ltd",
        status: "Active customer",
        accountCode: "CUS-00418",
        creditLimit: "USD 50,000",
        recentShipment: "OCN-2025-0847 · SIN→SYD",
        openQuotes: "1 (QT-2026-0138)",
      },
    };
  }

  return {
    status: "not_found",
    suggested: {
      companyName: input.displayName || input.domain,
      contactName: input.displayName || "",
      email: input.email,
      billingAddress: "",
    },
  };
}

/**
 * MOCK — swap for fetch('https://your-backend/create-customer', ...) later.
 */
export async function createCustomer(input: CustomerCreateInput): Promise<CustomerCreateResult> {
  await getAccessToken();
  await delay(1000);
  void input;
  return { customerId: "CUS-2026-0091" };
}
