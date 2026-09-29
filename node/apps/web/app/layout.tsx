import type { Metadata } from "next";
import { ClientRoot } from "@/main";
import "./styles.css";
export const metadata: Metadata = {
  title: "Frame / Lab",
  description: "Студия обработки изображений",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <ClientRoot>{children}</ClientRoot>
      </body>
    </html>
  );
}
