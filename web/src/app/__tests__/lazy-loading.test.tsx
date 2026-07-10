import React from 'react';
import { render, screen } from '@testing-library/react';
import { VocalinuxLogo } from '../../components/optimized-image';

const mockImage = jest.fn();
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    mockImage(props);
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { priority, loading, ...imgProps } = props;
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...imgProps} alt={props.alt} data-priority={priority} data-loading={loading} />;
  },
}));

describe('Lazy Loading Behavior', () => {
  beforeEach(() => {
    mockImage.mockClear();
  });

  describe('VocalinuxLogo Component', () => {
    it('lazy loads by default (no priority prop)', () => {
      render(<VocalinuxLogo />);
      const img = screen.getByAltText('Vocalinux');
      expect(img).toBeInTheDocument();
      expect(mockImage).toHaveBeenCalledWith(
        expect.objectContaining({
          priority: false,
        })
      );
    });

    it('eager loads when priority is true', () => {
      render(<VocalinuxLogo priority />);
      expect(mockImage).toHaveBeenCalledWith(
        expect.objectContaining({
          priority: true,
        })
      );
    });

    it('renders WebP source with PNG fallback', () => {
      const { container } = render(<VocalinuxLogo />);
      const source = container.querySelector('source');
      expect(source).toHaveAttribute('type', 'image/webp');
      expect(source?.getAttribute('srcset') || source?.getAttribute('srcSet')).toContain(
        'vocalinux.webp'
      );
      expect(mockImage).toHaveBeenCalledWith(
        expect.objectContaining({
          src: '/vocalinux.png',
        })
      );
    });
  });
});
