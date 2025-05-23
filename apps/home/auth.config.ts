import Auth0 from '@auth/core/providers/auth0';
import { defineConfig } from 'auth-astro';
import type { JWT } from '@auth/core/jwt';
import type { Session } from '@auth/core/types';

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
      issuer: import.meta.env.AUTH0_ISSUER,
      authorization: {
        params: {
          scope: 'openid profile email offline_access',
        },
      },
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
      } else {
      // If token has expired, try to refresh it
      if (extToken.refreshToken) {
        try {
          const response = await fetch(`${import.meta.env.AUTH0_ISSUER}/oauth/token`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
              grant_type: 'refresh_token',
              client_id: import.meta.env.AUTH0_CLIENT_ID,
              client_secret: import.meta.env.AUTH0_CLIENT_SECRET,
              refresh_token: extToken.refreshToken,
            }),
          });

          const tokens = await response.json();

          if (!response.ok) throw tokens;

          return {
            ...extToken,
            accessToken: tokens.access_token,
            accessTokenExpires: Date.now() + tokens.expires_in * 1000,
          };
        } catch (error) {
          console.error('Error refreshing access token', error);
          return {
            ...extToken,
            error: 'RefreshAccessTokenError',
          };
        }
      }
      // If there's no refresh token, return the token as is
      return extToken;
      }
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