const XLSX = require('xlsx');

// Excel template data
const templateData = [
  {
    'Yıl': 2024,
    'Ay': 1,
    'Elektrik (kWh)': 25000.5,
    'Su (m³)': 15000.2,
    'Doğalgaz (m³)': 8000.0,
    'Kömür (kg)': 0.0,
    'Dizel (lt)': 1200.0,
    'Benzin (lt)': 800.0,
    'LPG (kg)': 0.0,
    'Fuel Oil (lt)': 0.0,
    'R134a Gaz (kg)': 2.5,
    'R600a Gaz (kg)': 1.8,
    'R410a Gaz (kg)': 3.2,
    'R32 Gaz (kg)': 0.0,
    'CO2 Yangın (kg)': 0.0,
    'FM200 Yangın (kg)': 0.0,
    'Konaklama Sayısı': 250
  },
  {
    'Yıl': 2024,
    'Ay': 2,
    'Elektrik (kWh)': 22000.0,
    'Su (m³)': 14500.0,
    'Doğalgaz (m³)': 7500.0,
    'Kömür (kg)': 0.0,
    'Dizel (lt)': 1100.0,
    'Benzin (lt)': 750.0,
    'LPG (kg)': 0.0,
    'Fuel Oil (lt)': 0.0,
    'R134a Gaz (kg)': 2.0,
    'R600a Gaz (kg)': 1.5,
    'R410a Gaz (kg)': 3.0,
    'R32 Gaz (kg)': 0.0,
    'CO2 Yangın (kg)': 0.0,
    'FM200 Yangın (kg)': 0.0,
    'Konaklama Sayısı': 240
  },
  {
    'Yıl': 2024,
    'Ay': 3,
    'Elektrik (kWh)': 28000.0,
    'Su (m³)': 16000.0,
    'Doğalgaz (m³)': 9000.0,
    'Kömür (kg)': 500.0,
    'Dizel (lt)': 1300.0,
    'Benzin (lt)': 900.0,
    'LPG (kg)': 200.0,
    'Fuel Oil (lt)': 0.0,
    'R134a Gaz (kg)': 3.0,
    'R600a Gaz (kg)': 2.0,
    'R410a Gaz (kg)': 3.5,
    'R32 Gaz (kg)': 1.0,
    'CO2 Yangın (kg)': 0.0,
    'FM200 Yangın (kg)': 0.0,
    'Konaklama Sayısı': 260
  },
  {
    'Yıl': 2024,
    'Ay': 4,
    'Elektrik (kWh)': 30000.0,
    'Su (m³)': 17000.0,
    'Doğalgaz (m³)': 6000.0,
    'Kömür (kg)': 0.0,
    'Dizel (lt)': 1400.0,
    'Benzin (lt)': 950.0,
    'LPG (kg)': 150.0,
    'Fuel Oil (lt)': 0.0,
    'R134a Gaz (kg)': 2.8,
    'R600a Gaz (kg)': 1.9,
    'R410a Gaz (kg)': 3.8,
    'R32 Gaz (kg)': 0.8,
    'CO2 Yangın (kg)': 0.0,
    'FM200 Yangın (kg)': 0.0,
    'Konaklama Sayısı': 280
  },
  {
    'Yıl': 2024,
    'Ay': 5,
    'Elektrik (kWh)': 35000.0,
    'Su (m³)': 20000.0,
    'Doğalgaz (m³)': 4000.0,
    'Kömür (kg)': 0.0,
    'Dizel (lt)': 1600.0,
    'Benzin (lt)': 1100.0,
    'LPG (kg)': 300.0,
    'Fuel Oil (lt)': 100.0,
    'R134a Gaz (kg)': 3.5,
    'R600a Gaz (kg)': 2.5,
    'R410a Gaz (kg)': 4.0,
    'R32 Gaz (kg)': 1.2,
    'CO2 Yangın (kg)': 0.5,
    'FM200 Yangın (kg)': 0.0,
    'Konaklama Sayısı': 320
  },
  {
    'Yıl': 2024,
    'Ay': 6,
    'Elektrik (kWh)': 38000.0,
    'Su (m³)': 22000.0,
    'Doğalgaz (m³)': 3000.0,
    'Kömür (kg)': 0.0,
    'Dizel (lt)': 1800.0,
    'Benzin (lt)': 1200.0,
    'LPG (kg)': 400.0,
    'Fuel Oil (lt)': 150.0,
    'R134a Gaz (kg)': 4.0,
    'R600a Gaz (kg)': 3.0,
    'R410a Gaz (kg)': 4.5,
    'R32 Gaz (kg)': 1.5,
    'CO2 Yangın (kg)': 0.0,
    'FM200 Yangın (kg)': 0.0,
    'Konaklama Sayısı': 350
  }
];

// Create worksheet
const ws = XLSX.utils.json_to_sheet(templateData);

// Set column widths
ws['!cols'] = [
  { width: 6 },  // Yıl
  { width: 6 },  // Ay  
  { width: 15 }, // Elektrik
  { width: 12 }, // Su
  { width: 15 }, // Doğalgaz
  { width: 12 }, // Kömür
  { width: 12 }, // Dizel
  { width: 12 }, // Benzin
  { width: 12 }, // LPG
  { width: 15 }, // Fuel Oil
  { width: 15 }, // R134a Gaz
  { width: 15 }, // R600a Gaz
  { width: 15 }, // R410a Gaz
  { width: 12 }, // R32 Gaz
  { width: 15 }, // CO2 Yangın
  { width: 18 }, // FM200 Yangın
  { width: 18 }  // Konaklama Sayısı
];

// Create workbook and add worksheet
const wb = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb, ws, 'Tüketim Verileri');

// Add instructions sheet
const instructionsData = [
  ['GreenWave CRM - Toplu Tüketim Verisi İçe Aktarma Şablonu'],
  [''],
  ['KULLANIM TALİMATLARI:'],
  ['1. Bu dosyayı bilgisayarınıza kaydedin'],
  ['2. "Tüketim Verileri" sekmesindeki örnek verileri silin'],
  ['3. Kendi tüketim verilerinizi girin'],
  ['4. Dosyayı kaydedin (.xlsx formatında)'],
  ['5. CRM sisteminde "Toplu İçe Aktar" özelliğini kullanın'],
  [''],
  ['SÜTUN AÇIKLAMALARI:'],
  ['• Yıl: 4 haneli yıl (örn: 2024)'],
  ['• Ay: 1-12 arası ay numarası'],
  ['• Elektrik: kWh cinsinden elektrik tüketimi'],
  ['• Su: m³ cinsinden su tüketimi'],
  ['• Doğalgaz: m³ cinsinden doğalgaz tüketimi'],
  ['• Kömür: kg cinsinden kömür tüketimi'],
  ['• Dizel: Litre cinsinden dizel tüketimi'],
  ['• Benzin: Litre cinsinden benzin tüketimi'],
  ['• LPG: kg cinsinden LPG tüketimi'],
  ['• Fuel Oil: Litre cinsinden fuel oil tüketimi'],
  ['• R134a Gaz: kg cinsinden soğutucu gaz'],
  ['• R600a Gaz: kg cinsinden soğutucu gaz'],
  ['• R410a Gaz: kg cinsinden soğutucu gaz'],
  ['• R32 Gaz: kg cinsinden soğutucu gaz'],
  ['• CO2 Yangın: kg cinsinden CO2 yangın söndürücü'],
  ['• FM200 Yangın: kg cinsinden FM200 yangın söndürücü'],
  ['• Konaklama Sayısı: Aylık konaklayan kişi sayısı'],
  [''],
  ['DİKKAT EDİLMESİ GEREKENLER:'],
  ['• Tüm sayısal değerler ondalık olabilir (örn: 1234.56)'],
  ['• Boş alanlar 0 olarak kabul edilir'],
  ['• Aynı yıl/ay kombinasyonu varsa güncellenir'],
  ['• Hatalı veriler atlanır ve rapor edilir']
];

const instructionsWs = XLSX.utils.aoa_to_sheet(instructionsData);
instructionsWs['!cols'] = [{ width: 60 }];

XLSX.utils.book_append_sheet(wb, instructionsWs, 'Kullanım Talimatları');

// Write file
XLSX.writeFile(wb, '/app/frontend/public/tuketim_listesi_template.xlsx');

console.log('✅ Excel template created: /app/frontend/public/tuketim_listesi_template.xlsx');