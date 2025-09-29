import type React from "react"
import type { Metadata } from "next"
import { Suspense } from "react"
import "./globals.css"
import { Inter } from "next/font/google"

const arial = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-arial",
  fallback: ["Arial", "sans-serif"],
})

export const metadata: Metadata = {
  title: "ReQUESTA - Academic Question Generator",
  description: "Generate high-quality multiple-choice questions from academic texts using AI",
  generator: "ReQUESTA",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={arial.variable}>
      <body className="font-arial antialiased">
        <Suspense fallback={null}>{children}</Suspense>
      </body>
    </html>
  )
}
