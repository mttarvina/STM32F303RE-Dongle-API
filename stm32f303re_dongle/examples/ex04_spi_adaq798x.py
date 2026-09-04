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

    fs = 500_000
    adc_resolution = 16

    dongle = STM32F303RE_Dongle(port=com_port)
    dongle.spi_init(
        data_width=SPI_DataWidth.WIDTH_16,
        first_bit=SPI_FirstBit.MSB,
        freq=SPI_ClkFreq.CLK_18MHZ,
        clk_polarity=SPI_ClkPolarity.IDLE_LOW,
        clk_phase=SPI_ClkPhase.SECOND_EDGE,
        sample_rate=fs,
        transmit_delay=750e-9,
        csn_pulse_width=750e-9,
        csn_polarity=SPI_CSNPolarity.ACTIVE_HIGH,
    )

    num_samples = 1000
    dongle.spi_transmit(tx_command=[0xFFFF], frame_size=num_samples, increment=False)
    adc_data = np.array(dongle.buffer_read_rx(frame_size=num_samples))
    dynamic_range_db = ADC_ComputeDynamicRange(
        adc_samples=adc_data, resolution=adc_resolution
    )
    result = ADC_ComputeMetricsRaw(
        adc_samples=adc_data, fs=fs, resolution=adc_resolution
    )
    print(f"Dynamic Range: {dynamic_range_db} dB")

    plot = SignalPlotter(title="ADC Plots", size=(1920, 1080))
    plot.add_plot(
        title="ADC Raw Codes",
        x_label="Time",
        x_unit="s",
        x_data=np.linspace(0, ((1 / fs) * num_samples), num_samples, endpoint=False),
        y_label="Code",
        y_unit="",
        y_data=adc_data,
        y_range=(0, 2**adc_resolution),
        pen_color="#FFAA00",
    )
    plot.add_plot(
        title="Spectrum Magnitude (dBFS)",
        x_label="Frequency",
        x_unit="Hz",
        x_data=result["spectrum_freqs"],
        y_label="Magnitude",
        y_unit="dBFS",
        y_data=result["spectrum_mag_dbfs"],
        y_range=(-150, 0),
        pen_color="#FFAA00",
    )
    plot.add_text(
        text=f"f0: {result['f0']:.4f} Hz",
        plot_index=1,
        pos=(1600, 0),
        color="#00AAFF",
    )
    plot.add_text(
        text=f"f0_mag: {result['f0_mag']:.4f} dBFS",
        plot_index=1,
        pos=(1600, 15),
        color="#00AAFF",
    )
    plot.add_text(
        text=f"SNR: {result['snr']:.4f} dB",
        plot_index=1,
        pos=(1600, 30),
        color="#00AAFF",
    )
    plot.add_text(
        text=f"SINAD: {result['sinad']:.4f} dB",
        plot_index=1,
        pos=(1600, 45),
        color="#00AAFF",
    )
    plot.add_text(
        text=f"THD: {result['thd']:.4f} dB",
        plot_index=1,
        pos=(1600, 60),
        color="#00AAFF",
    )
    plot.add_text(
        text=f"ENOB: {result['enob']:.4f} dB",
        plot_index=1,
        pos=(1600, 75),
        color="#00AAFF",
    )
    plot.add_text(
        text=f"Peak Signal Level: {result['signal_level_pk']:.4f} dBFS",
        plot_index=1,
        pos=(1600, 90),
        color="#00AAFF",
    )
    plot.add_text(
        text=f"Average Signal Level: {result['signal_level_avg']:.4f} dBFS",
        plot_index=1,
        pos=(1600, 105),
        color="#00AAFF",
    )
    plot.show()


if __name__ == "__main__":
    main()
