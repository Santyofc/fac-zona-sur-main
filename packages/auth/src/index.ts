import NextAuth from "next-auth"
import { PrismaAdapter } from "@auth/prisma-adapter"
import { db } from "@factura-cr/db"

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(db),
  providers: [
    // Providers will be configured here
  ],
  callbacks: {
    async session({ session, user }) {
      // Custom session logic for multi-tenancy
      return session
    },
  },
  pages: {
    signIn: '/auth/login',
    error: '/auth/error',
  },
})
