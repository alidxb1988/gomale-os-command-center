import type { AppProps } from 'next/app';
import { Toaster } from 'react-hot-toast';
import Layout from '@/components/Layout';
import FloatingAIAgent from '@/components/ai-hub/FloatingAIAgent';
import { VoiceCommandProvider } from '@/contexts/VoiceCommandContext';
import '@/styles/globals.css';
import '@/lib/i18n';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <VoiceCommandProvider>
      <Layout>
        <Component {...pageProps} />
        <FloatingAIAgent />
        <Toaster 
          position="top-right"
          toastOptions={{
            style: {
              background: '#161b22',
              color: '#e6edf3',
              border: '1px solid #30363d',
            },
          }}
        />
      </Layout>
    </VoiceCommandProvider>
  );
}
