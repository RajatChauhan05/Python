import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk
import requests
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.dates import DateFormatter
import pyttsx3
import threading


class WeatherDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Data Dashboard")
        self.root.configure(bg='lightblue')

        # Initialize TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_thread = None
        self.stop_tts_flag = threading.Event()

        # Full screen dimensions
        scrn_width = 800 # self.root.winfo_screenwidth()
        scrn_height = 600 #self.root.winfo_screenheight()
        self.root.geometry(f"{scrn_width}x{scrn_height}+0+0")

        # Label and Combobox for City selection or entry
        self.city_label = tk.Label(root, text="Select or Enter City Name:", font=("Arial", 12), bg='#C4D7FF')
        self.city_label.pack(pady=5)

        self.cities = [
            "Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru",
            "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Chandigarh"
        ]
        self.city_combo = ttk.Combobox(root, values=self.cities, font=("Arial", 12))
        self.city_combo.set("Enter or select a city")
        self.city_combo.pack(pady=5)

        # Fetch Weather Data Button
        self.fetch_button = tk.Button(root, text="Fetch Weather Data", command=self.fetch_weather, font=("Arial", 12))
        self.fetch_button.pack(pady=1)

        # ScrolledText widget to display weather data
        self.data_display = scrolledtext.ScrolledText(root, width=50, height=30, font=("Arial", 10))
        self.data_display.pack(pady=1)

        # Speak and Stop Speaking Buttons
        self.speak_button = tk.Button(root, text="Speak Weather", command=self.start_speaking, font=("Arial", 12), bg='gray')
        self.speak_button.pack(pady=1)

        self.stop_button = tk.Button(root, text="Stop Speaking", command=self.stop_speaking, font=("Arial", 12), bg='red')
        self.stop_button.pack(pady=1)

        # Clear Data Button
        self.clear_button = tk.Button(root, text="Clear All Data", command=self.clear_all_data, font=("Arial", 12), bg='yellow')
        self.clear_button.pack(pady=5)

    def fetch_weather(self):
        """Fetch weather data for the selected city."""
        city = self.city_combo.get().strip()
        if not city or city == "Enter or select a city":
            messagebox.showwarning("Warning", "Please enter or select a valid city name.")
            return

        api_key = "a6f0ee5717157a4a27657b79c5d913cb"  # Replace with your API key
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data["cod"] != "200":
                messagebox.showerror("Error", f"City not found: {city}")
                return

            self.data_display.delete(1.0, tk.END)
            self.weather_info = ""

            dates, temperatures, humidities = [], [], []
            unique_days = set()

            # Limit to only the next 5 days
            for item in data['list']:
                date_obj = datetime.fromtimestamp(item['dt'])
                day_str = date_obj.strftime('%Y-%m-%d')

                if day_str not in unique_days:
                    temp = item['main']['temp']
                    humidity = item['main']['humidity']
                    description = item['weather'][0]['description']

                    entry = f"Date: {day_str}, Temp: {temp}°C, Humidity: {humidity}%, Condition: {description}\n"
                    self.data_display.insert(tk.END, entry)

                    self.weather_info += f"On {day_str}, the temperature is {temp} degrees Celsius with {description}. "
                    dates.append(date_obj)
                    temperatures.append(temp)
                    humidities.append(humidity)

                    unique_days.add(day_str)

                    # Stop if we have collected data for 5 days
                    if len(unique_days) == 5:
                        break

            self.plot_data(city, dates, temperatures, humidities)

        except requests.exceptions.HTTPError as http_err:
            messagebox.showerror("HTTP Error", f"HTTP error occurred: {http_err}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def start_speaking(self):
        """Start speaking weather data in a separate thread."""
        if hasattr(self, 'weather_info') and self.weather_info:
            self.speak_button.config(state=tk.DISABLED)
            self.stop_tts_flag.clear()
            self.tts_thread = threading.Thread(target=self.speak_weather)
            self.tts_thread.start()
        else:
            messagebox.showwarning("Warning", "No weather data to speak.")

    def speak_weather(self):
        """Speak the weather condition using TTS."""
        for sentence in self.weather_info.split('. '):
            if self.stop_tts_flag.is_set():
                break
            self.tts_engine.say(sentence)
            self.tts_engine.runAndWait()

        # Re-enable the Speak button after speech completes
        self.speak_button.config(state=tk.NORMAL)

    def stop_speaking(self):
        """Stop the TTS engine from speaking."""
        if self.tts_thread and self.tts_thread.is_alive():
            self.stop_tts_flag.set()
            self.tts_engine.stop()

        # Re-enable the Speak button after stopping
        self.speak_button.config(state=tk.NORMAL)

    def clear_all_data(self):
        """Clear all displayed data."""
        self.data_display.delete(1.0, tk.END)
        self.city_combo.set("Enter or select a city")
        self.weather_info = ""

    def plot_data(self, city, dates, temperatures, humidities):
        """Plot temperature and humidity data."""
        fig, ax1 = plt.subplots(figsize=(12, 6))

        ax1.set_xlabel("Date")
        ax1.set_ylabel("Temperature (°C)", color='tab:red')
        ax1.plot(dates, temperatures, color='tab:red', marker='o', linewidth=2, label='Temperature')
        ax1.tick_params(axis='y', labelcolor='tab:red')

        ax2 = ax1.twinx()
        ax2.set_ylabel("Humidity (%)", color='tab:blue')
        ax2.plot(dates, humidities, color='tab:blue', marker='o', linewidth=2, label='Humidity')
        ax2.tick_params(axis='y', labelcolor='tab:blue')

        date_format = DateFormatter("%d-%m")
        ax1.xaxis.set_major_formatter(date_format)
        plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

        plt.title(f"Weather Data for {city} (Next 5 Days)")
        fig.tight_layout()
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')

        plt.grid()
        plt.show()

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherDashboard(root)
   # root.iconbitmap("Weather.ico")
    root.mainloop()
