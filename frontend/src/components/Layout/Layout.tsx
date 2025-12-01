import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { StatusBar } from './StatusBar';

export const Layout: React.FC = () => {
  return (
    <div className="flex flex-col h-screen bg-ghost-950">
      <Header />
      <main className="flex-1 overflow-hidden pt-0">
        <Outlet />
      </main>
      <StatusBar />
    </div>
  );
};