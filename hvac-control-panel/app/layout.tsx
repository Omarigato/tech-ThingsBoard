import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Панель управления ПВУ | ORIONMETER AHU-01',
  description: 'Удаленный SCADA-мониторинг и телеметрия приточно-вытяжной установки',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
