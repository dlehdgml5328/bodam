/**
 * Button 컴포넌트 단위 테스트
 *
 * 테스트 커버리지:
 * - 기본 렌더링
 * - 클릭 이벤트 핸들링
 * - disabled 상태
 * - 다양한 variant (primary, secondary, outline)
 * - 로딩 상태
 * - 접근성 (a11y)
 */

import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

/**
 * Button 컴포넌트 (테스트용 간단한 구현)
 * 실제 프로젝트에서는 src/components/Button.tsx를 import
 */
interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: 'primary' | 'secondary' | 'outline'
  loading?: boolean
  type?: 'button' | 'submit' | 'reset'
  ariaLabel?: string
}

const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  disabled = false,
  variant = 'primary',
  loading = false,
  type = 'button',
  ariaLabel,
}) => {
  const baseClass = 'px-4 py-2 rounded font-medium transition-colors'
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700',
    outline: 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50',
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClass} ${variantClasses[variant]} ${
        disabled || loading ? 'opacity-50 cursor-not-allowed' : ''
      }`}
      aria-label={ariaLabel}
      data-testid="button"
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <span className="spinner" aria-hidden="true">
            ⏳
          </span>
          로딩 중...
        </span>
      ) : (
        children
      )}
    </button>
  )
}

/**
 * 테스트 스위트
 */
describe('Button 컴포넌트', () => {
  /**
   * 기본 렌더링 테스트
   */
  describe('렌더링', () => {
    it('children을 올바르게 렌더링한다', () => {
      render(<Button>클릭하세요</Button>)

      const button = screen.getByRole('button', { name: /클릭하세요/i })
      expect(button).toBeInTheDocument()
      expect(button).toHaveTextContent('클릭하세요')
    })

    it('aria-label이 제공되면 올바르게 적용된다', () => {
      render(<Button ariaLabel="제출 버튼">제출</Button>)

      const button = screen.getByRole('button', { name: /제출 버튼/i })
      expect(button).toBeInTheDocument()
    })

    it('기본 type은 button이다', () => {
      render(<Button>버튼</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'button')
    })

    it('type prop이 제공되면 올바르게 적용된다', () => {
      render(<Button type="submit">제출</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'submit')
    })
  })

  /**
   * 클릭 이벤트 테스트
   */
  describe('클릭 이벤트', () => {
    it('onClick 핸들러가 호출된다', () => {
      const handleClick = jest.fn()
      render(<Button onClick={handleClick}>클릭</Button>)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('userEvent로 클릭하면 onClick 핸들러가 호출된다', async () => {
      const handleClick = jest.fn()
      const user = userEvent.setup()
      render(<Button onClick={handleClick}>클릭</Button>)

      const button = screen.getByRole('button')
      await user.click(button)

      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('여러 번 클릭하면 onClick이 여러 번 호출된다', async () => {
      const handleClick = jest.fn()
      const user = userEvent.setup()
      render(<Button onClick={handleClick}>클릭</Button>)

      const button = screen.getByRole('button')
      await user.click(button)
      await user.click(button)
      await user.click(button)

      expect(handleClick).toHaveBeenCalledTimes(3)
    })
  })

  /**
   * disabled 상태 테스트
   */
  describe('disabled 상태', () => {
    it('disabled prop이 true일 때 버튼이 비활성화된다', () => {
      render(<Button disabled>비활성화</Button>)

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('disabled 상태에서는 onClick이 호출되지 않는다', async () => {
      const handleClick = jest.fn()
      const user = userEvent.setup()
      render(
        <Button onClick={handleClick} disabled>
          비활성화
        </Button>
      )

      const button = screen.getByRole('button')
      await user.click(button)

      expect(handleClick).not.toHaveBeenCalled()
    })

    it('disabled 상태에서 opacity-50 클래스가 적용된다', () => {
      render(<Button disabled>비활성화</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('opacity-50')
    })
  })

  /**
   * variant 스타일 테스트
   */
  describe('variant 스타일', () => {
    it('기본 variant는 primary이다', () => {
      render(<Button>Primary</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-blue-600', 'text-white')
    })

    it('variant="secondary"일 때 회색 배경이 적용된다', () => {
      render(<Button variant="secondary">Secondary</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-gray-600', 'text-white')
    })

    it('variant="outline"일 때 테두리 스타일이 적용된다', () => {
      render(<Button variant="outline">Outline</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('border-2', 'border-blue-600', 'text-blue-600')
    })
  })

  /**
   * 로딩 상태 테스트
   */
  describe('로딩 상태', () => {
    it('loading prop이 true일 때 로딩 텍스트가 표시된다', () => {
      render(<Button loading>제출</Button>)

      expect(screen.getByText(/로딩 중.../i)).toBeInTheDocument()
      expect(screen.queryByText('제출')).not.toBeInTheDocument()
    })

    it('loading 상태에서는 버튼이 비활성화된다', () => {
      render(<Button loading>제출</Button>)

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('loading 상태에서는 onClick이 호출되지 않는다', async () => {
      const handleClick = jest.fn()
      const user = userEvent.setup()
      render(
        <Button onClick={handleClick} loading>
          제출
        </Button>
      )

      const button = screen.getByRole('button')
      await user.click(button)

      expect(handleClick).not.toHaveBeenCalled()
    })

    it('loading 상태에서 스피너 아이콘이 표시된다', () => {
      render(<Button loading>제출</Button>)

      const spinner = screen.getByText('⏳')
      expect(spinner).toBeInTheDocument()
      expect(spinner).toHaveAttribute('aria-hidden', 'true')
    })
  })

  /**
   * 스냅샷 테스트
   */
  describe('스냅샷', () => {
    it('기본 렌더링 스냅샷과 일치한다', () => {
      const { container } = render(<Button>스냅샷 테스트</Button>)
      expect(container.firstChild).toMatchSnapshot()
    })

    it('disabled 상태 스냅샷과 일치한다', () => {
      const { container } = render(<Button disabled>비활성화</Button>)
      expect(container.firstChild).toMatchSnapshot()
    })

    it('loading 상태 스냅샷과 일치한다', () => {
      const { container } = render(<Button loading>로딩</Button>)
      expect(container.firstChild).toMatchSnapshot()
    })
  })
})
