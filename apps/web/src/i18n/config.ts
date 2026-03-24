export const supportedLocales = ["fr", "ar", "en"] as const;

export type SupportedLocale = (typeof supportedLocales)[number];
