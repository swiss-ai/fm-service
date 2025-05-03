// Authentication utilities for the Research Computer app

/**
 * Get the access token from storage or auth provider
 * In a real implementation, this would get the token from your auth provider library
 */
export async function getAccessToken(): Promise<string | null> {
  // In a real implementation, you would:
  // 1. Check if we have a valid token in localStorage/sessionStorage
  // 2. If the token is expired, refresh it
  // 3. Return the token
  
  // This is a simplified implementation
  return localStorage.getItem('accessToken');
}

/**
 * Store the access token
 */
export function setAccessToken(token: string): void {
  localStorage.setItem('accessToken', token);
}

/**
 * Remove the access token (for logout)
 */
export function clearAccessToken(): void {
  localStorage.removeItem('accessToken');
}

/**
 * Verify the access token with the backend and get user profile
 */
export async function verifyAccessToken(accessToken: string): Promise<any> {
  try {
    const response = await fetch('/api/auth/verify_token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ accessToken }),
    });
    
    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error verifying access token:', error);
    throw error;
  }
}

/**
 * Get user profile using the access token
 */
export async function getUserProfile(): Promise<any> {
  const accessToken = await getAccessToken();
  
  if (!accessToken) {
    throw new Error('No access token available');
  }
  
  try {
    const response = await fetch('/api/profile', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ accessToken }),
    });
    
    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching user profile:', error);
    throw error;
  }
}

/**
 * Make an authenticated API request using the access token
 */
export async function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const accessToken = await getAccessToken();
  
  if (!accessToken) {
    throw new Error('No access token available');
  }
  
  // Add the access token to the request headers
  const headers = new Headers(options.headers || {});
  headers.set('Authorization', `Bearer ${accessToken}`);
  
  // Make the request with the token
  return fetch(url, {
    ...options,
    headers,
  });
}

/**
 * Check if the user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    const accessToken = await getAccessToken();
    return !!accessToken;
  } catch (error) {
    return false;
  }
}