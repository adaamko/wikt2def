import os
from nltk.corpus import stopwords as nltk_stopwords

class Lexicon():
    
    def __init__(self, lang):
        self.lexicon = {}
        self.lang_map = {}
        base_fn = os.path.dirname(os.path.abspath(__file__))
        langnames_fn = os.path.join(base_fn, "langnames")
        definitions_fn = os.path.join(base_fn, "definitions/" + lang)

        with open(langnames_fn, "r") as f:
            for line in f:
                line = line.split("\t")
                self.lang_map[line[0]] = line[1].strip("\n")

        self.stopwords = set(nltk_stopwords.words(self.lang_map[lang]))

        with open(definitions_fn, "r") as f:
            for line in f:
                line = line.split("\t")
                if line[0].strip() not in self.lexicon:
                    self.lexicon[line[0].strip()] = line[2].strip().strip("\n")


    def expand(self, graph):
        for node in graph.get_nodes():
            print(node)


    # def expand_old(self, words_to_machines, cached=False, abstract=False):
    #     machines_to_append = []
    #     for lemma, machine in words_to_machines.iteritems():
    #         if (
    #                 (not cached or lemma not in self.expanded) and
    #                 lemma in self.known_words() and lemma not in stopwords):

    #             # deepcopy so that the version in the lexicon keeps its links
    #             definition = self.get_machine(lemma)

    #             copied_def = copy.deepcopy(definition)
    #             print("machine: " + str(machine))
    #             print("defintion: " + str(definition))
    #             if abstract is True:
    #                 part_one = False
    #                 part_two = False
    #                 if len(copied_def.partitions[1]) > 0:
    #                     if len(machine.partitions[1]) > 0:
    #                         part_one = True
    #                         print("machine partitions 1:")
    #                         for i in machine.partitions[1]:
    #                             print(i)
    #                             for j in copied_def.partitions[1]:
    #                                 for k in range(0,3):
    #                                     for m in j.partitions[k]:
    #                                         i.append(m,k)
    #                                 for p in j.parents:
    #                                     i.append(p[0], p[1])

    #                 if len(copied_def.partitions[2]) > 0:
    #                     if len(machine.partitions[2]) > 0:
    #                         part_two = True
    #                         print("machine partitions 2:")
    #                         for i in machine.partitions[2]:
    #                             for j in copied_def.partitions[2]:
    #                                 print(j)
    #                                 for k in range(0,3):
    #                                     for m in j.partitions[k]:
    #                                         i.append(m,k)
    #                                 for p in j.parents:
    #                                     i.append(p[0], p[1])

    #                 machine_for_replace = None
    #                 def_parents = [parent for parent in copied_def.parents if parent[1] == 0]

    #                 if len(copied_def.partitions[0]) > 0:
    #                     machine_for_replace = copied_def.partitions[0][0]
    #                 elif len(def_parents) > 0:
    #                     machine_for_replace = def_parents[0][0]
    #                 if machine_for_replace is not None:
    #                     for m in machine_for_replace.parents.copy():
    #                         if m[0].printname().startswith(lemma):
    #                             machine_for_replace.parents.remove(m)

    #                     for i in machine.parents.copy():
    #                         i[0].remove(machine,i[1])
    #                         i[0].append(machine_for_replace, i[1])

    #                     for i in range(0,3):
    #                         for m in machine.partitions[i]:
    #                             try:
    #                                 machine.remove(m, i)
    #                             except KeyError:
    #                                 pass
    #                             machine_for_replace.append(m, i)
    #                     machines_to_append.append(machine_for_replace)
    #                 if machine_for_replace is None and part_one is False and part_two is False:
    #                     pdb.set_trace()
    #                     machine_graph = [m for m in MachineTraverser.get_nodes(machine,names_only=False, keep_upper = True)]
    #                     def_graph = [m for m in MachineTraverser.get_nodes(copied_def,names_only=False, keep_upper = True)]
    #                     g1 = MachineGraph.create_from_machines(
    #                             machine_graph)
    #                     g2 = MachineGraph.create_from_machines(def_graph)
    #                     print("rossz machine: " + str(machine))
    #                     print("Definicio: " + str(copied_def))
    #                     print("Machine")
    #                     print(g1.to_dot())
    #                     print("Definicio")
    #                     print(g2.to_dot())
    #                     machine.unify(copied_def, exclude_0_case=True)
    #             else:
    #                 machine.unify(copied_def, exclude_0_case=True)

    #             #machine_for_replace.parents.remove((machine, 0))                
    #             '''
    #             print("machine for replace childs")
    #             for i in range(0,3):
    #                for m in machine_for_replace.partitions[i]:
    #                     print(m)
    #                     print(i)
    #             '''


    #             '''
    #             helpmachine = [
    #                 m for m in MachineTraverser.get_nodes(
    #                     copied_def, names_only=False, keep_upper=True)
    #                 ]
    #             '''

    #             """
    #             for parent, i in list(definition.parents):
    #                 copied_parent = copy.deepcopy(parent)
    #                 for m in list(copied_parent.partitions[i]):
    #                     if m.printname() == lemma:
    #                         copied_parent.remove(m, i)
    #                         break
    #                 else:
    #                     raise Exception()
    #                     # "can't find {0} in partition {1} of {2}: {3}".format(
    #                     # ))
    #                 copied_parent.append(copied_def, i)
    #             """

    #             case_machines = [
    #                 m for m in MachineTraverser.get_nodes(
    #                     copied_def, names_only=False, keep_upper=True)
    #                 if m.printname().startswith('=')] 


    #             #machine.unify(copied_def, exclude_0_case=True)
    #             for cm in case_machines:
    #                 if cm.printname() == "=AGT":
    #                     if machine.partitions[1]:
    #                         machine.partitions[1][0].unify(cm)
    #                 if cm.printname() == "=PAT":
    #                     if machine.partitions[2]:
    #                         machine.partitions[2][0].unify(cm)
    #             #for j in machine_for_replace.parents:
    #             #    print(j)                
    #             self.expanded.add(lemma)
    #     for m in machines_to_append:
    #         words_to_machines[m.printname()] = m


        