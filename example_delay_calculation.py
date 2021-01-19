"""
===============================================================================
Autor:      gary@duncodin.it
Date:       15/01/2021
Purpose:    Prototype algorithm for calculating delays on the SRN
Note:       *** DEMO CODE ONLY - N O T  F O R  P R O D U C T I O N ***
===============================================================================
"""

import numpy as np
import operator


class Midas_Measure:
    """Create a mock return type for the Midas Service"""

    link = ''
    date = ''
    lanes = 0
    time = ''
    speed1 = 0
    speed2 = 0
    speed3 = 0
    flow1 = 0
    flow2 = 0
    flow3 = 0


class Calc_Params:
    """Create a type to bind calculation params"""

    lanes_closed = 0
    length_of_closure_metres = 0
    duration_of_closure_mins = 0
    closure_speed_mph = 0


class App_Consts:
    """Create a type to hold some app constants"""

    metres_per_KM = 1000
    minutes_per_hour = 60
    shockwave_speed_KPH = 20
    shockwave_growth_metre_per_minute = 20000/60
    mc_iterations = 10000
    flex_percentage = 0.20
    threshold_certainty = 0.80


def get_midas_test_data() -> Midas_Measure:
    """Create a mock for the Midas Service"""

    m = Midas_Measure()
    m.link = 'A3-0413A'
    m.date = '24/01/2021'
    m.lanes = 3
    m.time = '10:00'
    m.speed1 = 109
    m.speed2 = 113
    m.speed3 = 113
    m.flow1 = 14
    m.flow2 = 11
    m.flow3 = 11

    return m


def mph2kph(mph: float) -> float:
    """Take a mph value and return the convertion to kph"""

    return mph * 1.609


def meters2KM(meters: float) -> float:
    """Take a value in meters and return the convertion to KM"""

    return meters / 1000


def sample_from_truncated_normal_distibution(_min: int, _max: int) -> float:
    """Take min and max value and return a single sample 
    from a normal distribution with the median point of the 
    range as the mean"""

    mean = _min + ((_max - _min)/2)
    std = ((_max-_min)/2)/3
    return (np.random.normal() * std) + mean


def get_distribution_sample_from_value(value: int, flexor: float) -> float:
    """Take a value and a float to create a range then return a sample from
    a truncated normal distribution over that range"""

    _min = value * (0 - flexor)
    _max = value * (1 + flexor)
    return sample_from_truncated_normal_distibution(_min, _max)


def record_result(result: int, store: dict) -> dict:
    """Take a result and a dict. If the dict has no 
    key for result, then add one and set the value to 0. 
    If the key already exists then increment the value 
    by one. Return the dict"""

    # Ensure result is rounded to nearest minute
    result = round(result)

    # Now record it
    if not result in store:
        store[result] = 0

    store[result] += 1

    return store


def get_range_for_threshold_certainty(freq_dist: dict, the_certainty: float) -> tuple:
    """Take a frequency distribution and return the range 
    that gives >= threshold certainty"""

    # Sort the freq_dist by count descending
    sorted_fd = {
        k: v for k, v in
        sorted(freq_dist.items(),
               key=lambda item: item[1],
               reverse=True)}

    # Get a list of keys in sorted order
    keys = list(sorted_fd.keys())

    # Short circuit if the first count has required certainty
    key = keys[0]
    count = sorted_fd[key]
    certainty = count/App_Consts.mc_iterations
    if certainty >= the_certainty:
        return (key, key, certainty)

    # Starting with the largest count, expand a window over the
    # counts until a range is establishsed that returns the certainty
    for stop in range(1, len(sorted_fd)):
        total = 0
        window = keys[:stop]
        for key in window:
            total += sorted_fd[key]
            certainty = total/App_Consts.mc_iterations
            if certainty >= the_certainty:
                return (min(window), max(window), certainty)

    # Threshold certainty not reached, so return the full range
    # Note: you shouldn't be able to get here.
    return (min(keys), max(keys), 1)


def get_total_flow_and_density_from_midas(midas: Midas_Measure) -> tuple:
    """Take a Midas_Measure and return a tuple of total flow and density"""

    total_flow = midas.flow1 + midas.flow2 + midas.flow3
    total_density = (
        (midas.flow1 / midas.speed1) +
        (midas.flow2 / midas.speed2) +
        (midas.flow3 / midas.speed3))

    return (total_flow, total_density)


def get_calc_params() -> Calc_Params:
    """Return an example set of calc params"""

    p = Calc_Params()
    p.lanes_closed = 2
    p.length_of_closure_metres = 250
    p.duration_of_closure_mins = 30
    p.closure_speed_mph = 50

    return p


def get_iteration_specific_midas_measure(
        m: Midas_Measure,
        ac: App_Consts) -> Midas_Measure:
    """Helper function which takes a Midas Measure and an App Constants and 
    returns a Midas Measure for a MC sim iteration."""

    m_temp = Midas_Measure()
    m_temp.lanes = m.lanes
    m_temp.flow1 = get_distribution_sample_from_value(
        m.flow1, ac.flex_percentage)

    m_temp.flow2 = get_distribution_sample_from_value(
        m.flow2, ac.flex_percentage)

    m_temp.flow3 = get_distribution_sample_from_value(
        m.flow3, ac.flex_percentage)

    m_temp.speed1 = get_distribution_sample_from_value(
        m.speed1, ac.flex_percentage)

    m_temp.speed2 = get_distribution_sample_from_value(
        m.speed2, ac.flex_percentage)

    m_temp.speed3 = get_distribution_sample_from_value(
        m.speed3, ac.flex_percentage)

    return m_temp


def get_iteration_specific_calc_params(
        p: Calc_Params,
        ac: App_Consts) -> Calc_Params:
    """Helper fuction which takes"""

    p_temp = Calc_Params()
    p_temp.lanes_closed = p.lanes_closed
    p_temp.length_of_closure_metres = get_distribution_sample_from_value(
        p.length_of_closure_metres, ac.flex_percentage)

    p_temp.duration_of_closure_mins = get_distribution_sample_from_value(
        p.duration_of_closure_mins, ac.flex_percentage)

    p_temp.closure_speed_mph = get_distribution_sample_from_value(
        p.closure_speed_mph, ac.flex_percentage)

    return p_temp


def run_mc_sim(ac: App_Consts, m: Midas_Measure, p: Calc_Params) -> dict:
    """Take an App Constants, a Midas Measure and a Calc Params, run
    an MC simulation and return the resutling frequency distribution"""

    results = {}
    for iteration in range(ac.mc_iterations):

        # Build an iteration specific Midas_Measure
        m_temp = get_iteration_specific_midas_measure(m, ac)

        # Build an iteration specific Calc_Params
        p_temp = get_iteration_specific_calc_params(p, ac)

        # Calculate the delay
        d_temp = calculate_delay(m_temp, p_temp)

        # Record the delay
        results = record_result(round(d_temp), results)

    # Return the results of the sim
    return results


def calculate_delay_full_closure(
        midas: Midas_Measure,
        params: Calc_Params) -> float:
    """Take a Midas_Mesasure and a Calc_Params and 
    return a calculated delay for a full closure"""

    # TODO: Calculate delay for full closure
    return -99.99


def calculate_delay(midas: Midas_Measure, params: Calc_Params) -> float:
    """Given a Midas_Measure and a Calc_Params return a calculated delay"""

    # Calculate total flow and total density
    total_flow, total_density = get_total_flow_and_density_from_midas(midas)

    # How many open lanes do we have?
    open_lanes = midas.lanes - params.lanes_closed

    # Handle the full closure case
    if open_lanes <= 0:
        return calculate_delay_full_closure(midas, params)

    # Closed lanes means increased denisty and reduced flow
    density_in_closure = total_density * (1 + (open_lanes / midas.lanes))
    flow_in_closure = total_flow * (1 - (open_lanes / midas.lanes))
    spacing_in_closure = 1/density_in_closure

    # TODO: Handle the max denisty exceeded case

    # Calculate the max speed through closure
    av_speed = flow_in_closure / density_in_closure

    # Take the smaller of speed in closure or restricted speed
    av_speed = min(av_speed, mph2kph(params.closure_speed_mph))

    """Calculate the total length of the incident as length of the closure + 
    the length of the shockwave. As per 
    https://en.wikipedia.org/wiki/Traffic_flow 
    the shockwave travels backwards at 20KPH"""
    length_shockwave_km = meters2KM(
        (App_Consts.shockwave_growth_metre_per_minute *
         params.duration_of_closure_mins))

    length_of_incident_km = (
        length_shockwave_km + meters2KM(params.length_of_closure_metres))

    # How long will it take to navigate the incident at that speed?
    time_to_navigate_incident = length_of_incident_km / av_speed

    # How long would if have taken to navigate the same distance
    # at the reported speed?
    av_reported_speed = (midas.speed1 + midas.speed2 + midas.speed3) / 3
    normal_time_to_navigate_incident = length_of_incident_km / av_reported_speed

    # Calculate and return the delay
    return (
        round(
            (time_to_navigate_incident - normal_time_to_navigate_incident) *
            App_Consts.minutes_per_hour, 2))


def main():
    """This is the application entry point"""

    # Get the Mides data
    m = get_midas_test_data()

    # Create some calculation params
    p = get_calc_params()

    # Calculate the delay
    d = calculate_delay(m, p)
    print(f'The calculated delay is {d} mintue(s)')

    # Run a Monte-Carlo simulation
    results = run_mc_sim(App_Consts, m, p)

    # Get the key (delay) and count with the highest frequency
    key = max(results.items(), key=operator.itemgetter(1))[0]
    count = results[key]
    certainty = count/App_Consts.mc_iterations
    print(
        f'The most likely delay will be {key} minute(s) ' +
        f'with {certainty} certainty')

    # Display range of threshold certainty
    start, stop, certainty = get_range_for_threshold_certainty(
        results,
        App_Consts.threshold_certainty)

    print(
        f'The delay will be between {start}' +
        f' minute(s) and {stop} minute(s) with {certainty} certainty')


if __name__ == "__main__" :
    main()
