import { useTranslation } from 'react-i18next';

function Settings({ settings, onSettingsChange, onClose, onLanguageChange, currentLanguage }) {
  const { t } = useTranslation();

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'zh', name: '中文' },
    { code: 'de', name: 'Deutsch' },
    { code: 'fr', name: 'Français' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 w-96">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">{t('settings')}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <span className="material-icons">close</span>
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <h3 className="font-medium mb-2">{t('general')}</h3>
            <div className="space-y-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('changeLanguage')}
                </label>
                <select
                  value={currentLanguage}
                  onChange={(e) => onLanguageChange(e.target.value)}
                  className="w-full p-2 border rounded-md"
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('model')}
                </label>
                <select
                  value={settings.model}
                  onChange={(e) => onSettingsChange({ ...settings, model: e.target.value })}
                  className="w-full p-2 border rounded-md"
                >
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="gpt-4">GPT-4</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('maxTokens')}
                </label>
                <input
                  type="number"
                  value={settings.maxTokens}
                  onChange={(e) => onSettingsChange({ ...settings, maxTokens: parseInt(e.target.value) })}
                  className="w-full p-2 border rounded-md"
                  min="1"
                  max="4000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('temperature')}
                </label>
                <input
                  type="number"
                  value={settings.temperature}
                  onChange={(e) => onSettingsChange({ ...settings, temperature: parseFloat(e.target.value) })}
                  className="w-full p-2 border rounded-md"
                  min="0"
                  max="1"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('topP')}
                </label>
                <input
                  type="number"
                  value={settings.topP}
                  onChange={(e) => onSettingsChange({ ...settings, topP: parseFloat(e.target.value) })}
                  className="w-full p-2 border rounded-md"
                  min="0"
                  max="1"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('maxHistorySize')}
                </label>
                <input
                  type="number"
                  value={settings.maxHistorySize}
                  onChange={(e) => onSettingsChange({ ...settings, maxHistorySize: parseInt(e.target.value) })}
                  className="w-full p-2 border rounded-md"
                  min="1"
                  max="100"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings; 