import React, { useState } from 'react';
import { useClerk } from '@clerk/clerk-react';

const ForgotPasswordPage = () => {
  const { client } = useClerk();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [step, setStep] = useState('request'); // 'request' | 'verify' | 'reset'
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleRequestReset = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setMessage('');

    try {
      // Clerk password reset isteği
      await client.signIn.create({
        strategy: 'reset_password_email_code',
        identifier: email,
      });
      
      setMessage('Şifre sıfırlama kodu email adresinize gönderildi.');
      setStep('verify');
    } catch (err) {
      console.error('Password reset request error:', err);
      setError('Şifre sıfırlama isteği gönderilemedi. Email adresinizi kontrol edin.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyCode = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const signInAttempt = await client.signIn.attemptFirstFactor({
        strategy: 'reset_password_email_code',
        code: code,
      });

      if (signInAttempt.status === 'needs_new_password') {
        setStep('reset');
        setMessage('Kod doğrulandı. Yeni şifrenizi oluşturun.');
      }
    } catch (err) {
      console.error('Code verification error:', err);
      setError('Kod doğrulanamadı. Tekrar deneyin.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      setError('Şifreler eşleşmiyor.');
      return;
    }

    if (newPassword.length < 8) {
      setError('Şifre en az 8 karakter olmalıdır.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await client.signIn.resetPassword({
        password: newPassword,
      });
      
      setMessage('Şifreniz başarıyla değiştirildi! Giriş sayfasına yönlendiriliyorsunuz...');
      
      // 2 saniye sonra giriş sayfasına yönlendir
      setTimeout(() => {
        window.location.href = '/sign-in';
      }, 2000);
    } catch (err) {
      console.error('Password reset error:', err);
      setError('Şifre değiştirilemedi. Tekrar deneyin.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-500 via-emerald-600 to-teal-700 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo ve Header */}
        <div className="text-center mb-8">
          <img 
            src="/greenwave-logo.png" 
            alt="GreenWave CRM" 
            className="w-24 h-24 mx-auto mb-4 object-contain"
          />
          <h1 className="text-3xl font-bold text-white mb-2">
            Şifremi Unuttum
          </h1>
          <p className="text-green-100 text-lg">
            Şifrenizi sıfırlayın
          </p>
        </div>

        {/* Form Container */}
        <div className="bg-white/95 backdrop-blur-lg rounded-2xl p-8 shadow-2xl border border-white/20">
          
          {/* Step 1: Email isteği */}
          {step === 'request' && (
            <form onSubmit={handleRequestReset} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Adresi
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full p-4 border-2 border-green-200 rounded-xl focus:border-green-500 focus:outline-none transition-colors"
                  placeholder="Email adresinizi girin"
                  required
                />
              </div>
              
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white py-4 rounded-xl font-semibold hover:from-green-600 hover:to-emerald-700 transition-all duration-300 disabled:opacity-50"
              >
                {isLoading ? 'Gönderiliyor...' : 'Sıfırlama Kodu Gönder'}
              </button>
            </form>
          )}

          {/* Step 2: Kod doğrulama */}
          {step === 'verify' && (
            <form onSubmit={handleVerifyCode} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Doğrulama Kodu
                </label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full p-4 border-2 border-green-200 rounded-xl focus:border-green-500 focus:outline-none transition-colors text-center text-lg tracking-wider"
                  placeholder="6 haneli kodu girin"
                  maxLength="6"
                  required
                />
                <p className="text-sm text-gray-600 mt-2">
                  {email} adresine gönderilen kodu girin
                </p>
              </div>
              
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white py-4 rounded-xl font-semibold hover:from-green-600 hover:to-emerald-700 transition-all duration-300 disabled:opacity-50"
              >
                {isLoading ? 'Doğrulanıyor...' : 'Kodu Doğrula'}
              </button>
              
              <button
                type="button"
                onClick={() => setStep('request')}
                className="w-full text-green-600 py-2 text-sm hover:text-green-700 transition-colors"
              >
                ← Email adresini değiştir
              </button>
            </form>
          )}

          {/* Step 3: Yeni şifre */}
          {step === 'reset' && (
            <form onSubmit={handleResetPassword} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Yeni Şifre
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full p-4 border-2 border-green-200 rounded-xl focus:border-green-500 focus:outline-none transition-colors"
                  placeholder="Yeni şifrenizi girin"
                  minLength="8"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Şifre Tekrarı
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full p-4 border-2 border-green-200 rounded-xl focus:border-green-500 focus:outline-none transition-colors"
                  placeholder="Şifrenizi tekrar girin"
                  minLength="8"
                  required
                />
              </div>
              
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white py-4 rounded-xl font-semibold hover:from-green-600 hover:to-emerald-700 transition-all duration-300 disabled:opacity-50"
              >
                {isLoading ? 'Değiştiriliyor...' : 'Şifremi Değiştir'}
              </button>
            </form>
          )}

          {/* Mesajlar */}
          {message && (
            <div className="mt-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded-xl text-sm">
              {message}
            </div>
          )}
          
          {error && (
            <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-xl text-sm">
              {error}
            </div>
          )}

          {/* Geri dön linki */}
          <div className="mt-6 text-center">
            <a 
              href="/sign-in" 
              className="text-green-600 hover:text-green-700 font-medium text-sm transition-colors"
            >
              ← Giriş sayfasına dön
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;