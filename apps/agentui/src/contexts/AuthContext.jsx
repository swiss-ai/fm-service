import { createContext, useContext, useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const { isAuthenticated, getAccessTokenSilently, loginWithRedirect, logout, user } = useAuth0();
  const [swissAIToken, setSwissAIToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const getSwissAIToken = async () => {
      if (isAuthenticated) {
        try {
          console.log('Getting Auth0 access token...');
          const accessToken = await getAccessTokenSilently();
          console.log('Auth0 access token received');
          
          console.log('Fetching SwissAI profile...');
          const response = await fetch('https://api.swissai.cscs.ch/v1/profile', {
            headers: {
              'Authorization': `Bearer ${accessToken}`
            }
          });
          
          if (!response.ok) {
            const errorText = await response.text();
            console.error('SwissAI profile response not OK:', response.status, errorText);
            throw new Error(`Failed to fetch SwissAI token: ${response.status} ${errorText}`);
          }
          
          const data = await response.json();
          console.log('SwissAI profile received:', data);
          setSwissAIToken(data.api_key);
        } catch (error) {
          console.error('Error in getSwissAIToken:', error);
          setSwissAIToken(null);
        }
      } else {
        console.log('User not authenticated');
        setSwissAIToken(null);
      }
      setIsLoading(false);
    };

    getSwissAIToken();
  }, [isAuthenticated, getAccessTokenSilently]);

  const value = {
    isAuthenticated,
    isLoading,
    swissAIToken,
    login: loginWithRedirect,
    logout: () => logout({ returnTo: window.location.origin }),
    user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 