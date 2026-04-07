"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { themeConfig } from "../../lib/theme";

type HeaderButtonProps = {
  href: string;
  children: ReactNode;
};

function HeaderButton({ href, children }: HeaderButtonProps) {
  return (
    <Link
      href={href}
      className="inline-flex h-9 items-center justify-center rounded-button border border-white/20 px-3 text-sm font-medium text-kinnoo-text transition hover:border-[#FF7F00] hover:text-[#FF7F00] max-[399px]:px-2 max-[399px]:text-xs"
      style={{ borderRadius: themeConfig.radii.button }}
    >
      {children}
    </Link>
  );
}

type MainLayoutProps = {
  children: ReactNode;
};

export default function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-kinnoo-bg text-kinnoo-text">
      <header
        className="sticky top-0 z-50 border-b border-white/10 glass-surface"
        style={{
          borderColor: themeConfig.colors.cardBorder,
          color: themeConfig.colors.text,
        }}
      >
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-2 px-4 py-3">
          <div className="flex items-center gap-3">
            <Dialog.Root>
              <Dialog.Trigger asChild>
                <button
                  type="button"
                  aria-label="Open menu"
                  className="inline-flex h-10 w-10 items-center justify-center rounded-button border border-white/20 text-kinnoo-text transition hover:border-white/30"
                  style={{ borderRadius: themeConfig.radii.button }}
                >
                  <Menu size={18} />
                </button>
              </Dialog.Trigger>

              <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/60" />
                <Dialog.Content
                  className="fixed top-16 rounded-card border border-white/10 bg-[#222222] p-4 shadow-xl"
                  style={{
                    borderColor: themeConfig.colors.cardBorder,
                    left: "max(1rem, calc((100vw - 72rem) / 2 + 1rem))",
                    width: "min(20rem, calc(100vw - 2rem))",
                  }}
                >
                  <div className="mb-4 flex items-center justify-between">
                    <Dialog.Title className="text-base font-semibold">Menu</Dialog.Title>
                    <Dialog.Description className="sr-only">
                      Quick navigation links for project resources.
                    </Dialog.Description>
                    <Dialog.Close asChild>
                      <button
                        type="button"
                        aria-label="Close menu"
                        className="inline-flex h-8 w-8 items-center justify-center rounded-button border border-white/20"
                      >
                        <X size={16} />
                      </button>
                    </Dialog.Close>
                  </div>
                  <nav className="flex flex-col gap-3 text-sm">
                    <a href="https://github.com/kinnoo-project/kinnoo" target="_blank" rel="noreferrer">
                      GitHub
                    </a>
                    <a
                      href="https://github.com/kinnoo-project/kinnoo/tree/main/docs"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Docs
                    </a>
                    <a href="https://github.com/kinnoo-project/kinnoo/issues" target="_blank" rel="noreferrer">
                      Report an Issue
                    </a>
                  </nav>
                </Dialog.Content>
              </Dialog.Portal>
            </Dialog.Root>

            <Link
              href="/"
              className="text-lg font-medium tracking-wide text-kinnoo-text transition hover:text-[#FF7F00] sm:text-xl"
            >
              kinnoo
            </Link>
          </div>

          <div className="flex shrink-0 items-center gap-1 sm:gap-2">
            <HeaderButton href="/login">Login</HeaderButton>
            <HeaderButton href="/signup">Sign Up</HeaderButton>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
