// app/components/Sidebar.tsx
import React, { ReactNode } from "react";

interface SidebarProps {
  children?: ReactNode;
}

export default function Sidebar({ children }: SidebarProps) {
  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Sidebar</h2>
      <p>Navigation or additional controls here.</p>
      {children}
    </div>
  );
}
