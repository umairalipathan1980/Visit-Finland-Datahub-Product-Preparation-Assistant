import { Geist, Geist_Mono } from "next/font/google"

import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { SiteHeader } from "@/components/shared/site-header"
import { RunMonitor } from "@/components/shared/run-monitor"
import { Toaster } from "@/components/ui/sonner"
import { cn } from "@/lib/utils";
import type { Metadata } from "next"

const geist = Geist({subsets:['latin'],variable:'--font-sans'})

const fontMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

export const metadata: Metadata = {
  title: "DataHub Studio — Product preparation",
  description: "Turn company sources into a reviewable Visit Finland DataHub product record.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn("antialiased", fontMono.variable, "font-sans", geist.variable)}
    >
      <body>
        <ThemeProvider>
          <RunMonitor />
          <SiteHeader />
          <main className="mx-auto max-w-4xl px-6 py-10">{children}</main>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}
