import dns
import clientsubnetoption


def query_and_resolve(domain, qtype, iter=False, dns_server="223.5.5.5"):

    def resolve(dns_message, qtype):
        ans = []
        if dns_message is None:
            return ans
        dns_message = dns_message.to_text()
        if ";ANSWER" in dns_message:
            lines = dns_message.split("\n")
            answer_reached = False

            for line in lines:
                if answer_reached:
                    res = line.split()[-1]
                    if f"IN {qtype}" in line:
                        ans.append(res)
                    elif "IN" not in line:
                        break
                elif line == ";ANSWER":
                    answer_reached = True
        return ans

    def query(domain, qtype):
        try:
            message = dns.message.make_query(domain, qtype)
            dns_message = dns.query.udp(message, dns_server)
            ans = resolve(dns_message, qtype)

        except Exception as e:
            print(e)
            ans = []
        return ans

    if qtype.upper() == "CNAME" and iter:
        cname = domain
        prev_ans = []

        while True:
            print(cname)
            ans = query(cname, qtype)
            if (not prev_ans) and (not ans):
                return prev_ans
            elif prev_ans and (not ans):
                return prev_ans
            else:
                cname = ans[0]
                prev_ans = ans
    else:
        ans = query(domain, qtype)
    return ans
