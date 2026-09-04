import time

import numpy as np
from signals_toolkit import (
    ADC_ComputeDynamicRange,
    ADC_ComputeMetricsRaw,
    SignalPlotter,
)

from stm32f303re_dongle import (
    STM32F303RE_Dongle,
    scan_stlink,
)
from stm32f303re_dongle.dongle import (
    SPI_ClkFreq,
    SPI_ClkPhase,
    SPI_ClkPolarity,
    SPI_CSNPolarity,
    SPI_DataWidth,
    SPI_FirstBit,
)


def main():
    com_port = scan_stlink()
    if com_port is None:
        raise RuntimeError("No STM32/STLINK found!")

    fs = 800_000
    adc_resolution = 12
    dongle = STM32F303RE_Dongle(port=com_port)
    dongle.spi_init(
        data_width=SPI_DataWidth.WIDTH_16,
        first_bit=SPI_FirstBit.MSB,
        freq=SPI_ClkFreq.CLK_18MHZ,
        clk_polarity=SPI_ClkPolarity.IDLE_HIGH,
        clk_phase=SPI_ClkPhase.FIRST_EDGE,
        sample_rate=fs,
        transmit_delay=0,
        csn_pulse_width=1.0e-6,
        csn_polarity=SPI_CSNPolarity.ACTIVE_LOW,
    )
    startup_sequence = [0xFFFF, 0xFFFF, 0x8310, 0x8310, 0x8310]
    dongle.spi_transmit(
        tx_command=startup_sequence, frame_size=len(startup_sequence), increment=True
    )
    time.sleep(0.5)

    num_samples = 6144
    ignore_samples = 6
    t_axis = np.linspace(0, ((1 / fs) * num_samples), num_samples, endpoint=False)
    plot_width = 1600
    plot_height = 900
    text_loc = int(0.8 * plot_width)

    plot = SignalPlotter(title="ADC Plots", size=(plot_width, plot_height))
    plot.add_plot(
        title="ADC Raw Codes",
        x_label="Time",
        x_unit="s",
        x_data=t_axis,
        y_label="Code",
        y_unit="",
        y_data=np.zeros(num_samples),
        y_range=(0, 2**adc_resolution),
        pen_color="#FFAA00",
    )
    plot.add_plot(
        title="Spectrum Magnitude (dBFS)",
        x_label="Frequency",
        x_unit="Hz",
        x_data=np.linspace(0, (fs / 2), int((num_samples / 2) + 1), endpoint=False),
        y_label="Magnitude",
        y_unit="dBFS",
        y_data=np.zeros(int((num_samples / 2) + 1)),
        y_range=(-150, 0),
        pen_color="#FF00AA",
    )

    plot.add_text("-", 1, (text_loc, 0), "#00AAFF")  # text index 0
    plot.add_text("-", 1, (text_loc, 15), "#00AAFF")  # text index 1
    plot.add_text("-", 1, (text_loc, 30), "#00AAFF")  # text index 2
    plot.add_text("-", 1, (text_loc, 45), "#00AAFF")  # text index 3
    plot.add_text("-", 1, (text_loc, 60), "#00AAFF")  # text index 4
    plot.add_text("-", 1, (text_loc, 75), "#00AAFF")  # text index 5
    plot.add_text("-", 1, (text_loc, 90), "#00AAFF")  # text index 6

    def stream_plot():
        dongle.spi_transmit(
            tx_command=[0x8310],
            frame_size=num_samples + ignore_samples,
            increment=False,
        )
        adc_data = np.array(
            dongle.buffer_read_rx(frame_size=num_samples + ignore_samples)
        )[ignore_samples:]
        dynamic_range_db = ADC_ComputeDynamicRange(
            adc_samples=adc_data, resolution=adc_resolution
        )
        result = ADC_ComputeMetricsRaw(
            adc_samples=adc_data, fs=fs, resolution=adc_resolution
        )
        # print(f"Dynamic Range: {dynamic_range_db} dB")
        plot.update_plot(index=0, x_data=t_axis, y_data=adc_data)
        plot.update_plot(
            index=1,
            x_data=result["spectrum_freqs"],
            y_data=result["spectrum_mag_dbfs"],
        )
        plot.update_text(index=0, text=f"f0 : {result['f0']:.2f} Hz")
        plot.update_text(index=1, text=f"f0 Magnitude : {result['f0_mag']:.2f} dBFS")
        plot.update_text(index=2, text=f"SNR : {result['snr']:.2f} dB")
        plot.update_text(index=3, text=f"SINAD : {result['sinad']:.2f} dB")
        plot.update_text(index=4, text=f"THD : {result['thd']:.2f} dB")
        plot.update_text(index=5, text=f"ENOB : {result['enob']:.2f} bits")
        plot.update_text(index=6, text=f"Dynamic Range: {dynamic_range_db:.2f} dB")

    plot.setup_stream(plot_interval=0.2, callback_fn=stream_plot)
    plot.start_stream()

    plot.show()


if __name__ == "__main__":
    main()
