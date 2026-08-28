import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Vaga Certa · Mobilidade PUC-Rio',
  description: 'Previsão transparente de ocupação e caronas para a comunidade PUC-Rio.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
