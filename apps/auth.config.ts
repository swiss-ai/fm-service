import Auth0 from '@auth/core/providers/auth0';
import { defineConfig } from 'auth-astro';
import type { JWT } from '@auth/core/jwt';
import type { Session } from '@auth/core/types';

console.log("Auth0 Client ID:", import.meta.env.AUTH0_CLIENT_ID);

// Define custom types for our extended token and session
interface ExtendedJWT extends JWT {
  accessToken?: string;
  refreshToken?: string;
  accessTokenExpires?: number;
  user?: any;
}

interface ExtendedSession extends Session {
  accessToken?: string;
}

export default defineConfig({
  providers: [
    Auth0({
      clientId: import.meta.env.AUTH0_CLIENT_ID,
      clientSecret: import.meta.env.AUTH0_CLIENT_SECRET,
      issuer: process.env.AUTH0_ISSUER
    }),
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      const extToken = token as ExtendedJWT;
      
      // If we have user and account info (after sign in), add the access token to the token
      if (account && user) {
        return {
          ...extToken,
          accessToken: account.access_token,
          refreshToken: account.refresh_token,
          accessTokenExpires: account.expires_at ? account.expires_at * 1000 : 0,
          user,
        };
      }

      // If token hasn't expired, return it
      if (extToken.accessTokenExpires && Date.now() < extToken.accessTokenExpires) {
        return extToken;
      }
      
      // Otherwise, return the existing token (refresh token logic would go here if implemented)
      return extToken;
    },
    
    async session({ session, token }) {
      const extToken = token as ExtendedJWT;
      const extSession = session as ExtendedSession;
      
      // Add the access token and user to the session
      if (extToken) {
        extSession.accessToken = extToken.accessToken;
        if (extToken.user) {
          extSession.user = {
            ...extSession.user,
            ...extToken.user
          };
        }
      }
      return extSession;
    }
  }
});