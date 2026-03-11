import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '../components/Button.tsx';

const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    
    try {
      if (isLogin) {
        await login({ email, password });
      } else {
        await register({ name, email, password });
      }
      navigate('/');
    } catch (error: any) {
        setErrorMessage(error.message || 'An authentication error occurred');
    } finally {
        setIsLoading(false);
    }
  };

  const inputErrorClasses = errorMessage
    ? "border-destructive focus:border-destructive focus:ring-destructive"
    : "border-border focus:border-ring focus:ring-ring";

  const handleChange = (setter: React.Dispatch<React.SetStateAction<string>>) => (e: React.ChangeEvent<HTMLInputElement>) => {
      setter(e.target.value);
      if (errorMessage) setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="w-full max-w-md p-8 space-y-8 bg-card rounded-lg shadow-lg border border-border">
        <div>
          <h2 className="text-center text-3xl font-extrabold text-foreground">
            {isLogin ? 'Sign in to your account' : 'Create a new account'}
          </h2>
        </div>

        {errorMessage && (
            <div role="alert" aria-live="assertive" className="bg-destructive/10 border-l-4 border-destructive text-destructive p-4 mb-4 rounded shadow-sm flex items-start">
                <div className="flex-1">
                    <p className="font-bold">Error</p>
                    <p className="text-sm">{errorMessage}</p>
                </div>
            </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {!isLogin && (
            <div>
              <label htmlFor="name" className="sr-only">Name</label>
              <input
                id="name"
                name="name"
                type="text"
                required
                className={`appearance-none rounded-md relative block w-full px-3 py-2 border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-2 focus:z-10 sm:text-sm ${inputErrorClasses}`}
                placeholder="Full Name"
                value={name}
                onChange={handleChange(setName)}
                aria-invalid={!!errorMessage}
              />
            </div>
          )}
          <div>
            <label htmlFor="email-address" className="sr-only">Email address</label>
            <input
              id="email-address"
              name="email"
              type="email"
              autoComplete="email"
              required
              className={`appearance-none rounded-md relative block w-full px-3 py-2 border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-2 focus:z-10 sm:text-sm ${inputErrorClasses}`}
              placeholder="Email address"
              value={email}
              onChange={handleChange(setEmail)}
              aria-invalid={!!errorMessage}
            />
          </div>
          <div>
            <label htmlFor="password" className="sr-only">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              className={`appearance-none rounded-md relative block w-full px-3 py-2 border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-2 focus:z-10 sm:text-sm ${inputErrorClasses}`}
              placeholder="Password"
              value={password}
              onChange={handleChange(setPassword)}
              aria-invalid={!!errorMessage}
            />
          </div>
          
          <div>
            <Button
              type="submit"
              isLoading={isLoading}
              className="w-full"
              variant="primary"
            >
              {isLogin ? 'Sign in' : 'Sign up'}
            </Button>
          </div>
        </form>
        <div className="text-sm text-center">
          <button
            type="button"
            onClick={() => { setIsLogin(!isLogin); setErrorMessage(null); }}
            className="font-medium text-primary hover:text-primary/90"
          >
            {isLogin ? 'Don\'t have an account? Sign up' : 'Already have an account? Sign in'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
