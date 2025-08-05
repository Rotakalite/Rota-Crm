import React from 'react';
import { SignUp } from '@clerk/clerk-react';

const CustomSignUp = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-500 via-emerald-600 to-teal-700 flex items-center justify-center p-4">
      {/* Custom Logo ve Header */}
      <div className="w-full max-w-md">
        {/* Logo ve Başlık */}
        <div className="text-center mb-8">
          <img 
            src="/greenwave-logo.png" 
            alt="GreenWave CRM" 
            className="w-24 h-24 mx-auto mb-4 object-contain"
          />
          <h1 className="text-3xl font-bold text-white mb-2">
            GreenWave CRM
          </h1>
          <p className="text-green-100 text-lg">
            Hesap Oluşturun
          </p>
          <p className="text-green-100 text-sm mt-2">
            Sürdürülebilirlik yönetimi için hemen başlayın
          </p>
        </div>

        {/* Clerk Sign Up Component */}
        <div className="bg-white/95 backdrop-blur-lg rounded-2xl p-8 shadow-2xl border border-white/20">
          <SignUp 
            appearance={{
              elements: {
                // Ana container'ı temizle
                rootBox: {
                  background: 'transparent',
                  boxShadow: 'none',
                  border: 'none',
                },
                card: {
                  background: 'transparent',
                  boxShadow: 'none',
                  border: 'none',
                  padding: 0,
                },
                // Başlığı gizle
                headerTitle: {
                  display: 'none',
                },
                headerSubtitle: {
                  display: 'none',
                },
                // Form elemanları
                formButtonPrimary: {
                  background: 'linear-gradient(135deg, #10b981 0%, #047857 100%)',
                  borderRadius: '12px',
                  padding: '14px 28px',
                  fontSize: '16px',
                  fontWeight: '600',
                  boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)',
                  transition: 'all 0.3s ease',
                  border: 'none',
                  width: '100%',
                  marginTop: '1rem',
                },
                formFieldInput: {
                  borderRadius: '12px',
                  border: '2px solid #d1fae5',
                  padding: '14px 16px',
                  fontSize: '16px',
                  transition: 'all 0.3s ease',
                  backgroundColor: 'white',
                },
                formFieldLabel: {
                  color: '#374151',
                  fontWeight: '500',
                  marginBottom: '0.5rem',
                  fontSize: '14px',
                },
                // Footer linkler
                footerActionText: {
                  color: '#6b7280',
                  textAlign: 'center',
                  marginTop: '1.5rem',
                },
                footerActionLink: {
                  color: '#10b981',
                  fontWeight: '600',
                  textDecoration: 'none',
                },
                // Sosyal login butonları
                socialButtonsIconButton: {
                  borderRadius: '12px',
                  border: '2px solid #10b981',
                  transition: 'all 0.3s ease',
                  marginBottom: '0.5rem',
                },
                // Terms and conditions
                identityPreviewText: {
                  fontSize: '14px',
                  color: '#6b7280',
                },
                identityPreviewEditButton: {
                  color: '#10b981',
                },
              },
              variables: {
                colorPrimary: '#10b981',
                colorText: '#1f2937',
                colorTextSecondary: '#6b7280',
                fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                borderRadius: '12px',
              },
            }}
            // Routing ayarları
            routing="path"
            path="/sign-up"
            signInUrl="/sign-in"
            // Custom fields
            additionalOAuthScopes={{
              google: ['email', 'profile'],
            }}
          />
        </div>

        {/* Alt bilgi */}
        <p className="text-center text-green-100 text-sm mt-6">
          Kayıt olarak <span className="font-semibold">Kullanım Şartları</span> ve{' '}
          <span className="font-semibold">Gizlilik Politikası</span>'nı kabul etmiş olursunuz.
        </p>
      </div>
    </div>
  );
};

export default CustomSignUp;