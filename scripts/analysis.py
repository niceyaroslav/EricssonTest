import pandas as pd
import datetime


class Analysis:
    """This code was made in a hurry and doesn't represent author's full potential."""
    def __init__(self):
        """Data loading"""
        self.missions = pd.read_excel('data/missions.xlsx')
        self.orders = pd.read_excel('data/OrderSheet.xlsx')
        self.robots = pd.read_excel('data/robot.xlsx')
        self.routes = pd.read_excel('data/Routes.xlsx')

        """Adjustment of data types and filtering"""
        self.orders['UserRequestTime'] = pd.to_datetime(self.orders['UserRequestTime'])
        self.orders['RecTime'] = pd.to_datetime(self.orders['RecTime'])
        self.missions['Ordered'] = pd.to_datetime(self.missions['Ordered'])
        self.route_missions = [i.strip() for i in self.routes['Mission']]
        self.transition_start = datetime.datetime.strptime('2020-03-09', '%Y-%m-%d')
        self.transition_end = self.get_transition_period_end()
        self.total_filtered_missions = pd.concat([self.missions[self.missions['Ordered'] < self.transition_start],
                                                  self.missions[self.missions['Ordered'] > self.transition_end]])
        self.total_filtered_missions['Message'] = [i.strip() for i in self.total_filtered_missions['Message']]
        self.total_filtered_missions['Mission'] = [i.strip() for i in self.total_filtered_missions['Mission']]
        self.total_filtered_orders = pd.concat([self.orders[self.orders['RecTime'] < self.transition_start],
                                                self.orders[self.orders['RecTime'] > self.transition_end]])
        self.total_filtered_missions['Shift'] = self.generate_shift_parameter()
        self.robot_dict = dict(zip(self.robots['Robot_id'], self.robots['Robot']))

    def generate_shift_parameter(self):
        shift = []
        shift_start = datetime.datetime.strptime('07:30:00', '%H:%M:%S').time()
        shift_end = datetime.datetime.strptime('19:30:00', '%H:%M:%S').time()
        for i in self.total_filtered_missions['Ordered']:
            if shift_start <= i.time() < shift_end:
                shift.append('Day')
            else:
                shift.append('Night')
        return shift

    def get_order_counts(self):
        ords = self.total_filtered_orders[self.total_filtered_orders['TrolleyID'].notna()]
        lines = list(ords['ProdLine'])
        line_counts = {}
        for i in lines:
            if i not in line_counts.keys():
                line_counts[i] = 0
            else:
                line_counts[i] += 1
        return line_counts

    def get_routing_missions(self):
        rm = dict()
        for i, j in self.missions.iterrows():
            for k in self.route_missions:
                if k in j['Mission']:
                    rm[j['Mission_ID']] = {"Robot_id": j['Robot_id'],
                                           "Mission": j['Mission'].strip(),
                                           "Message": j['Message'].strip(),
                                           "Ordered": j['Ordered']}
        return rm

    def get_transition_period_end(self):
        transitioning = []
        for _, j in self.get_routing_missions().items():
            if j['Ordered'] > self.transition_start and 'Tartu' in j['Mission']:
                transitioning.append(j['Ordered'])
        end_date = max(set(transitioning))
        return end_date

    def get_faulty_missions(self):
        f_missions = self.total_filtered_missions['Message'].str.contains("ActionList was executed without problems..")
        faulty = self.total_filtered_missions[~f_missions]
        faulty = faulty[faulty['Message'] != '']
        return faulty

    def evaluate_robot_usage(self):
        l_c = self.get_order_counts()
        robot_lines = set(self.routes['ProdLine'].to_list())
        robot_orders = []
        human_orders = []
        for k, v in l_c.items():
            if k in robot_lines:
                robot_orders.append(v)
            else:
                human_orders.append(v)
        total_orders = sum([sum(human_orders), sum(robot_orders)])
        # usage_df = pd.DataFrame({"Robot orders": [round(sum(robot_orders) * 100/total_orders, 2)],
        #                          "Human orders": [round(sum(human_orders) * 100/total_orders, 2)]})
        usage_df = pd.DataFrame({'Type': ['Robot orders', 'Human orders'],
                                 'Value': [round(sum(robot_orders) * 100 / total_orders, 2),
                                           round(sum(human_orders) * 100 / total_orders, 2)]})
        return usage_df

    def evaluate_failure_rate(self):
        success = len(self.total_filtered_missions) - len(self.get_faulty_missions())
        total = len(self.total_filtered_missions)
        fail = pd.DataFrame({'Type': ['Successful', 'Failed'],
                             'Value': [round(success * 100 / total, 2),
                                       round(len(self.get_faulty_missions()) * 100 / total, 2)]})
        return fail

    def quantify_and_analyze_fails(self):
        fails = self.get_faulty_missions()['Message'].value_counts()
        fail_data = dict()
        for i, j in fails.items():
            if 'Abort' not in i and j > 8:
                fail_data[i] = j
        return pd.DataFrame({'Problems': fail_data.keys(),
                             'Occurence': fail_data.values()})

    def get_pct_aborted(self):
        fails = self.get_faulty_missions()['Message'].value_counts()
        aborts = [0]
        other_issues = [0]
        for i, j in fails.items():
            if 'Abort' in i:
                aborts[0] += j
            else:
                other_issues[0] += j
        return pd.DataFrame({'Type': ['Aborted', 'Other issues'],
                             'Value': [round((aborts[0] * 100 / (aborts[0] + other_issues[0])), 2),
                                       round((other_issues[0] * 100 / (aborts[0] + other_issues[0])), 2)]})

    def get_total_usage_by_robot(self):
        counts = []
        df = self.total_filtered_missions
        df = df.loc[:, ['Robot_id', 'Shift']]
        rc = df['Robot_id'].value_counts()
        for k, v in rc.items():
            shifts = df[df['Robot_id'] == k].value_counts()
            if (k, 'Night') in shifts.keys():
                counts.append({'Robot': self.robot_dict[k],
                               'Day': shifts[(k, 'Day')],
                               'Night': shifts[(k, 'Night')]})
            else:
                counts.append({'Robot': self.robot_dict[k],
                               'Day': shifts[(k, 'Day')],
                               'Night': 0})
        ress = pd.DataFrame(counts)
        ress['Share of Day missions'] = round(ress['Day'] * 100 / sum(ress['Day']), 2)
        ress['Share of Night missions'] = round(ress['Night'] * 100 / sum(ress['Night']), 2)
        return ress

    def prepare_df_for_fail_mapping(self, aborted):
        df = self.get_faulty_missions()
        f = df['Message'].str.contains('Abort')
        if aborted:
            dff = df[f]
        else:
            dff = df[~f]
        # Prepare aborted missions df
        dff = dff.loc[:, ['Robot_id', 'Shift']]
        rc = dff['Robot_id'].value_counts()
        res = []
        # shifts = dff[dff['Robot_id'] == 14].value_counts()
        for k, v in rc.items():
            shifts = dff[dff['Robot_id'] == k].value_counts()
            if (k, 'Night') in shifts.keys():
                res.append({'Robot': self.robot_dict[k],
                            'Day': shifts[(k, 'Day')],
                            'Night': shifts[(k, 'Night')]})
            else:
                res.append({'Robot': self.robot_dict[k],
                            'Day': shifts[(k, 'Day')],
                            'Night': 0})
        ress = pd.DataFrame(res)
        ress['Share of Day failures'] = round(ress['Day'] * 100 / sum(ress['Day']), 2)
        ress['Share of Night failures'] = round(ress['Night'] * 100 / sum(ress['Night']), 2)
        return ress
        # return shifts


if __name__ == '__main__':
    analysis = Analysis()
    c = analysis.total_filtered_missions
    all_missions = analysis.missions
    orders = analysis.orders
    robots = analysis.robots
    routes = analysis.routes
    routing_missions = analysis.get_routing_missions()
    faulty_missions = analysis.get_faulty_missions()
    # Analysis block
    filtered_orders = analysis.total_filtered_orders

    rm = c[c['Mission'].isin(analysis.route_missions)]
    kek = analysis.evaluate_robot_usage()
    qf = analysis.quantify_and_analyze_fails()
    pa = analysis.get_pct_aborted()
    oc = analysis.prepare_df_for_fail_mapping(aborted=False)
    aoc = analysis.prepare_df_for_fail_mapping(aborted=True)
    tub = analysis.get_total_usage_by_robot()