import { ReactNode } from 'react';

type CardPadding = 'sm' | 'md' | 'lg';

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: CardPadding;
  shadow?: boolean;
  hover?: boolean;
}

export default function Card({
  children,
  className = '',
  padding = 'md',
  shadow = true,
  hover = false,
}: CardProps) {
  const paddingClasses: Record<CardPadding, string> = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={`bg-white rounded-xl border border-gray-100 ${shadow ? 'shadow-lg' : ''} ${
        hover ? 'hover:shadow-xl transition-shadow duration-300' : ''
      } ${paddingClasses[padding]} ${className}`}
    >
      {children}
    </div>
  );
}
