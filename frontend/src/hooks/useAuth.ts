import { useState, useEffect } from 'react';
import { supabase } from '../supabase';
import { getMyMerchant, createMerchant } from '../api';
import type { User, Session } from '@supabase/supabase-js';

interface Merchant {
  id: string;
  business_name: string;
  auth_user_id: string;
  cost_floor: number;
  max_retry_attempts: number;
}

interface AuthState {
  user: User | null;
  session: Session | null;
  merchant: Merchant | null;
  loading: boolean;
}

export function useAuth(): AuthState {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [merchant, setMerchant] = useState<Merchant | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMerchant = async (userId?: string) => {
    try {
      const m = await getMyMerchant();
      setMerchant(m);
    } catch (e: any) {
      // 404 = merchant row wasn't created during signup (e.g. Render cold start)
      // Auto-create it now
      if (e?.response?.status === 404 && userId) {
        try {
          const { data } = await supabase.auth.getSession();
          const user = data.session?.user;
          if (user) {
            const m = await createMerchant({
              auth_user_id: user.id,
              business_name: user.email?.split('@')[0] || 'My Business',
            });
            setMerchant(m);
          }
        } catch {
          setMerchant(null);
        }
      } else {
        setMerchant(null);
      }
    }
  };

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setUser(data.session?.user ?? null);
      if (data.session) fetchMerchant(data.session.user.id).finally(() => setLoading(false));
      else setLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session) fetchMerchant(session.user.id);
      else setMerchant(null);
    });

    return () => listener.subscription.unsubscribe();
  }, []);

  return { user, session, merchant, loading };
}
