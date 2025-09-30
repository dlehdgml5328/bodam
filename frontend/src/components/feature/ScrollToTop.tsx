'use client';

import { useState, useEffect } from 'react';

export default function ScrollToTop() {
  const [isVisible, setIsVisible] = useState(false);

  const buttonClassName = [
    'fixed bottom-8 right-8 z-50',
    'flex h-12 w-12 items-center justify-center',
    'rounded-full bg-red-600 text-white',
    'shadow-lg transition-all duration-200',
    'hover:bg-red-700 hover:shadow-xl',
    'group',
  ].join(' ');

  const iconClassName = [
    'ri-arrow-up-line text-xl',
    'transform transition-transform duration-200',
    'group-hover:-translate-y-0.5',
  ].join(' ');

  useEffect(() => {
    const toggleVisibility = () => {
      if (window.pageYOffset > 300) {
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    };

    window.addEventListener('scroll', toggleVisibility);

    return () => window.removeEventListener('scroll', toggleVisibility);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  };

  if (!isVisible) {
    return null;
  }

  return (
    <button
      onClick={scrollToTop}
      className={buttonClassName}
      aria-label="맨 위로 가기"
    >
      <i className={iconClassName}></i>
    </button>
  );
}
